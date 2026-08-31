import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from re import fullmatch
from uuid import UUID

import httpx
from pydantic import ValidationError

from woonlens.adapters.sources.pdok.property_models import (
    BuildingFeature,
    ResidentialUnitCollection,
)
from woonlens.application.errors import (
    PropertyDetailsNotFoundError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.property import Building, PropertyDetails, ResidentialUnit


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _raise_for_provider_status(response: httpx.Response) -> None:
    if response.status_code == 404:
        raise PropertyDetailsNotFoundError
    if response.status_code == 429:
        raise SourceRateLimitedError
    if response.status_code >= 500:
        raise SourceUnavailableError
    if response.is_error:
        raise SourceContractError


def _use_purposes(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    purposes = tuple(part.strip() for part in value.split(",") if part.strip())
    if len(purposes) != len(set(purposes)):
        raise SourceContractError
    return purposes


class PdokBagPropertyAdapter:
    """Fetch a BAG verblijfsobject and its related pand records."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        *,
        max_related_buildings: int,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._max_related_buildings = max_related_buildings
        self._clock = clock

    async def fetch(self, addressable_object_id: str) -> PropertyDetails:
        if fullmatch(r"\d{16}", addressable_object_id) is None:
            raise SourceContractError
        response = await self._get(
            f"{self._base_url}/collections/verblijfsobject/items",
            params={
                "identificatie": addressable_object_id,
                "limit": 2,
                "f": "json",
            },
        )
        try:
            collection = ResidentialUnitCollection.model_validate(response.json())
        except (ValidationError, ValueError) as exc:
            raise SourceContractError from exc
        if collection.number_returned != len(collection.features):
            raise SourceContractError
        if not collection.features:
            raise PropertyDetailsNotFoundError
        if len(collection.features) != 1:
            raise SourceContractError

        feature = collection.features[0]
        properties = feature.properties
        if properties.identificatie != addressable_object_id:
            raise SourceContractError
        building_ids = self._building_ids(properties.pand_hrefs or [])
        if len(building_ids) > self._max_related_buildings:
            raise SourceContractError

        building_features = await asyncio.gather(
            *(self._fetch_building(building_id) for building_id in building_ids)
        )
        return PropertyDetails(
            residential_unit=ResidentialUnit(
                id=properties.identificatie,
                status=properties.status,
                use_purposes=_use_purposes(properties.gebruiksdoel),
                registered_area_m2=properties.oppervlakte,
            ),
            buildings=tuple(
                Building(
                    id=building.properties.identificatie,
                    status=building.properties.status,
                    construction_year=building.properties.bouwjaar,
                    use_purposes=_use_purposes(building.properties.gebruiksdoel),
                    residential_unit_count=(
                        building.properties.aantal_verblijfsobjecten
                    ),
                )
                for building in building_features
            ),
            source=SourceMetadata(
                provider="PDOK / Kadaster",
                dataset="Basisregistratie Adressen en Gebouwen",
                retrieved_at=self._clock(),
                license_name="Public Domain Mark 1.0",
            ),
        )

    def _building_ids(self, hrefs: list[str]) -> tuple[UUID, ...]:
        expected_prefix = f"{self._base_url}/collections/pand/items/"
        ids: list[UUID] = []
        for href in hrefs:
            if not href.startswith(expected_prefix):
                raise SourceContractError
            suffix = href.removeprefix(expected_prefix)
            if "/" in suffix or "?" in suffix or "#" in suffix:
                raise SourceContractError
            try:
                ids.append(UUID(suffix))
            except ValueError as exc:
                raise SourceContractError from exc
        if len(ids) != len(set(ids)):
            raise SourceContractError
        return tuple(ids)

    async def _fetch_building(self, building_id: UUID) -> BuildingFeature:
        response = await self._get(
            f"{self._base_url}/collections/pand/items/{building_id}",
            params={"f": "json"},
        )
        try:
            feature = BuildingFeature.model_validate(response.json())
        except (ValidationError, ValueError) as exc:
            raise SourceContractError from exc
        if feature.id != building_id:
            raise SourceContractError
        return feature

    async def _get(
        self,
        url: str,
        *,
        params: dict[str, str | int],
    ) -> httpx.Response:
        try:
            response = await self._client.get(url, params=params)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise SourceUnavailableError from exc
        _raise_for_provider_status(response)
        return response
