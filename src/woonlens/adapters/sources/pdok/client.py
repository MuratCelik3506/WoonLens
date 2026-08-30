from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

import httpx
from pydantic import ValidationError

from woonlens.adapters.sources.pdok.models import (
    BagAddressFeature,
    LocationSearchResponse,
)
from woonlens.application.errors import (
    AddressNotFoundError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _raise_for_provider_status(response: httpx.Response) -> None:
    if response.status_code == 404:
        raise AddressNotFoundError
    if response.status_code == 429:
        raise SourceRateLimitedError
    if response.status_code >= 500:
        raise SourceUnavailableError
    if response.is_error:
        raise SourceContractError


class PdokLocationSearchAdapter:
    """Search the current PDOK Location API address collection."""

    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def suggest(self, query: str, *, limit: int) -> tuple[AddressSuggestion, ...]:
        try:
            response = await self._client.get(
                f"{self._base_url}/search",
                params={
                    "q": query,
                    "adres[version]": 1,
                    "limit": limit,
                    "f": "json",
                },
            )
        except httpx.TimeoutException as exc:
            raise SourceUnavailableError from exc
        except httpx.NetworkError as exc:
            raise SourceUnavailableError from exc

        _raise_for_provider_status(response)
        try:
            payload = LocationSearchResponse.model_validate(response.json())
        except (ValidationError, ValueError) as exc:
            raise SourceContractError from exc

        if payload.numberReturned != len(payload.features):
            raise SourceContractError

        source = SourceMetadata(
            provider="PDOK",
            dataset="Location API address collection v1",
            retrieved_at=payload.timestamp,
            license_name="CC BY 4.0",
        )
        return tuple(
            AddressSuggestion(
                id=feature.id,
                display_name=feature.properties.display_name,
                coordinates=Coordinates(
                    longitude=feature.geometry.coordinates[0],
                    latitude=feature.geometry.coordinates[1],
                ),
                source=source,
            )
            for feature in payload.features
        )


class PdokBagAddressAdapter:
    """Resolve one known address UUID through PDOK's BAG OGC API."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._clock = clock

    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        try:
            response = await self._client.get(
                f"{self._base_url}/collections/adres/items/{address_id}",
                params={"f": "json"},
            )
        except httpx.TimeoutException as exc:
            raise SourceUnavailableError from exc
        except httpx.NetworkError as exc:
            raise SourceUnavailableError from exc

        _raise_for_provider_status(response)
        try:
            feature = BagAddressFeature.model_validate(response.json())
        except (ValidationError, ValueError) as exc:
            raise SourceContractError from exc

        if feature.id != address_id:
            raise SourceContractError

        properties = feature.properties
        return ResolvedAddress(
            id=feature.id,
            number_designation_id=properties.identificatie,
            addressable_object_id=properties.adresseerbaar_object_identificatie,
            addressable_object_type=properties.adresseerbaar_object_type,
            street=properties.openbare_ruimte_naam,
            house_number=properties.huisnummer,
            house_letter=properties.huisletter,
            house_number_suffix=properties.toevoeging,
            postal_code=properties.postcode,
            city=properties.woonplaats_naam,
            coordinates=Coordinates(
                longitude=feature.geometry.coordinates[0],
                latitude=feature.geometry.coordinates[1],
            ),
            source=SourceMetadata(
                provider="PDOK",
                dataset="BAG OGC API address collection",
                retrieved_at=self._clock(),
                license_name="Public Domain Mark 1.0",
            ),
        )
