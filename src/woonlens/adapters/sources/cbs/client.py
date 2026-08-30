import asyncio
from collections.abc import Sequence

import httpx
from pydantic import ValidationError

from woonlens.adapters.sources.cbs.models import (
    NeighborhoodCollection,
    ProvinceCollection,
)
from woonlens.application.errors import (
    AdministrativeContextNotFoundError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import Coordinates, SourceMetadata
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext

_BBOX_MARGIN = 0.0000001


def _raise_for_provider_status(response: httpx.Response) -> None:
    if response.status_code == 429:
        raise SourceRateLimitedError
    if response.status_code >= 500:
        raise SourceUnavailableError
    if response.is_error:
        raise SourceContractError


class CbsAdministrativeContextAdapter:
    """Join current CBS area boundaries around one CRS84 coordinate."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        neighborhoods_url: str,
        regions_url: str,
        *,
        dataset_year: int,
    ) -> None:
        self._client = client
        self._neighborhoods_url = neighborhoods_url.rstrip("/")
        self._regions_url = regions_url.rstrip("/")
        self._dataset_year = dataset_year

    async def resolve(self, coordinates: Coordinates) -> AdministrativeContext:
        bbox = ",".join(
            str(value)
            for value in (
                coordinates.longitude - _BBOX_MARGIN,
                coordinates.latitude - _BBOX_MARGIN,
                coordinates.longitude + _BBOX_MARGIN,
                coordinates.latitude + _BBOX_MARGIN,
            )
        )
        neighborhood_response, province_response = await asyncio.gather(
            self._get(
                f"{self._neighborhoods_url}/collections/buurten/items",
                {"bbox": bbox, "limit": 2, "f": "json"},
            ),
            self._get(
                f"{self._regions_url}/collections/provincie_gegeneraliseerd/items",
                {
                    "bbox": bbox,
                    "jaarcode": self._dataset_year,
                    "limit": 2,
                    "f": "json",
                },
            ),
        )
        try:
            neighborhoods = NeighborhoodCollection.model_validate(
                neighborhood_response.json()
            )
            provinces = ProvinceCollection.model_validate(province_response.json())
        except (ValidationError, ValueError) as exc:
            raise SourceContractError from exc

        self._validate_collection(neighborhoods.number_returned, neighborhoods.features)
        self._validate_collection(provinces.number_returned, provinces.features)
        if not neighborhoods.features and not provinces.features:
            raise AdministrativeContextNotFoundError

        neighborhood = neighborhoods.features[0] if neighborhoods.features else None
        province = provinces.features[0] if provinces.features else None
        if (
            neighborhood is not None
            and int(neighborhood.properties.jaar) != self._dataset_year
        ):
            raise SourceContractError
        if province is not None and province.properties.jaarcode != self._dataset_year:
            raise SourceContractError

        sources: list[SourceMetadata] = []
        if neighborhood is not None:
            sources.append(
                SourceMetadata(
                    provider="PDOK",
                    dataset=f"CBS Wijken en Buurten {self._dataset_year}",
                    retrieved_at=neighborhoods.timestamp,
                    license_name="CC BY 4.0",
                )
            )
        if province is not None:
            sources.append(
                SourceMetadata(
                    provider="PDOK",
                    dataset="CBS Gebiedsindelingen 2016 to present",
                    retrieved_at=provinces.timestamp,
                    license_name="CC BY 4.0",
                )
            )

        properties = neighborhood.properties if neighborhood is not None else None
        return AdministrativeContext(
            neighborhood=(
                AdministrativeArea(properties.bu_code, properties.bu_naam)
                if properties is not None
                else None
            ),
            district=(
                AdministrativeArea(properties.wk_code, properties.wk_naam)
                if properties is not None
                else None
            ),
            municipality=(
                AdministrativeArea(properties.gm_code, properties.gm_naam)
                if properties is not None
                else None
            ),
            province=(
                AdministrativeArea(
                    province.properties.statcode,
                    province.properties.statnaam,
                )
                if province is not None
                else None
            ),
            sources=tuple(sources),
        )

    async def _get(
        self,
        url: str,
        params: dict[str, str | int],
    ) -> httpx.Response:
        try:
            response = await self._client.get(url, params=params)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise SourceUnavailableError from exc
        _raise_for_provider_status(response)
        return response

    @staticmethod
    def _validate_collection(count: int, features: Sequence[object]) -> None:
        if count != len(features) or len(features) > 1:
            raise SourceContractError
