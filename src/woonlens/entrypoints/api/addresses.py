from datetime import datetime
from typing import Annotated, Self, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from woonlens.application.services.addresses import AddressService
from woonlens.application.services.administrative import AdministrativeContextService
from woonlens.application.services.indicators import NeighborhoodIndicatorsService
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators

router = APIRouter(prefix="/addresses", tags=["addresses"])


class CoordinatesResponse(BaseModel):
    longitude: float
    latitude: float
    crs: str

    @classmethod
    def from_domain(cls, coordinates: Coordinates) -> Self:
        return cls(
            longitude=coordinates.longitude,
            latitude=coordinates.latitude,
            crs=coordinates.crs,
        )


class SourceResponse(BaseModel):
    provider: str
    dataset: str
    retrieved_at: datetime
    license: str

    @classmethod
    def from_domain(cls, source: SourceMetadata) -> Self:
        return cls(
            provider=source.provider,
            dataset=source.dataset,
            retrieved_at=source.retrieved_at,
            license=source.license_name,
        )


class AddressSuggestionResponse(BaseModel):
    id: UUID
    display_name: str
    coordinates: CoordinatesResponse
    source: SourceResponse

    @classmethod
    def from_domain(cls, suggestion: AddressSuggestion) -> Self:
        return cls(
            id=suggestion.id,
            display_name=suggestion.display_name,
            coordinates=CoordinatesResponse.from_domain(suggestion.coordinates),
            source=SourceResponse.from_domain(suggestion.source),
        )


class AddressSuggestionsResponse(BaseModel):
    items: list[AddressSuggestionResponse]


class ResolvedAddressResponse(BaseModel):
    id: UUID
    number_designation_id: str
    addressable_object_id: str
    addressable_object_type: str
    street: str
    house_number: str
    house_letter: str | None
    house_number_suffix: str | None
    postal_code: str
    city: str
    coordinates: CoordinatesResponse
    source: SourceResponse

    @classmethod
    def from_domain(cls, address: ResolvedAddress) -> Self:
        return cls(
            id=address.id,
            number_designation_id=address.number_designation_id,
            addressable_object_id=address.addressable_object_id,
            addressable_object_type=address.addressable_object_type,
            street=address.street,
            house_number=address.house_number,
            house_letter=address.house_letter,
            house_number_suffix=address.house_number_suffix,
            postal_code=address.postal_code,
            city=address.city,
            coordinates=CoordinatesResponse.from_domain(address.coordinates),
            source=SourceResponse.from_domain(address.source),
        )


class AdministrativeAreaResponse(BaseModel):
    code: str
    name: str

    @classmethod
    def from_domain(cls, area: AdministrativeArea | None) -> Self | None:
        return cls(code=area.code, name=area.name) if area is not None else None


class AdministrativeContextResponse(BaseModel):
    neighborhood: AdministrativeAreaResponse | None
    district: AdministrativeAreaResponse | None
    municipality: AdministrativeAreaResponse | None
    province: AdministrativeAreaResponse | None
    sources: list[SourceResponse]

    @classmethod
    def from_domain(cls, context: AdministrativeContext) -> Self:
        return cls(
            neighborhood=AdministrativeAreaResponse.from_domain(context.neighborhood),
            district=AdministrativeAreaResponse.from_domain(context.district),
            municipality=AdministrativeAreaResponse.from_domain(context.municipality),
            province=AdministrativeAreaResponse.from_domain(context.province),
            sources=[SourceResponse.from_domain(source) for source in context.sources],
        )


class NeighborhoodIndicatorResponse(BaseModel):
    key: str
    measure_id: str
    label: str
    value: float | None
    unit: str
    source_unit: str
    missing_reason: str | None

    @classmethod
    def from_domain(cls, indicator: NeighborhoodIndicator) -> Self:
        return cls(
            key=indicator.key,
            measure_id=indicator.measure_id,
            label=indicator.label,
            value=indicator.value,
            unit=indicator.unit,
            source_unit=indicator.source_unit,
            missing_reason=indicator.missing_reason,
        )


class NeighborhoodIndicatorsResponse(BaseModel):
    level: str = "neighborhood"
    neighborhood: AdministrativeAreaResponse
    dataset_id: str
    dataset_year: int
    indicators: list[NeighborhoodIndicatorResponse]
    source: SourceResponse

    @classmethod
    def from_domain(cls, result: NeighborhoodIndicators) -> Self:
        neighborhood = AdministrativeAreaResponse.from_domain(result.neighborhood)
        if neighborhood is None:
            raise ValueError("neighborhood is required")
        return cls(
            neighborhood=neighborhood,
            dataset_id=result.dataset_id,
            dataset_year=result.dataset_year,
            indicators=[
                NeighborhoodIndicatorResponse.from_domain(indicator)
                for indicator in result.indicators
            ],
            source=SourceResponse.from_domain(result.source),
        )


def get_address_service(request: Request) -> AddressService:
    return cast(AddressService, request.app.state.address_service)


def get_administrative_context_service(
    request: Request,
) -> AdministrativeContextService:
    return cast(
        AdministrativeContextService,
        request.app.state.administrative_context_service,
    )


def get_neighborhood_indicators_service(
    request: Request,
) -> NeighborhoodIndicatorsService:
    return cast(
        NeighborhoodIndicatorsService,
        request.app.state.neighborhood_indicators_service,
    )


@router.get("/suggest", response_model=AddressSuggestionsResponse)
async def suggest_addresses(
    request: Request,
    q: Annotated[str, Query(min_length=2, max_length=200)],
) -> AddressSuggestionsResponse:
    suggestions = await get_address_service(request).suggest(q)
    return AddressSuggestionsResponse(
        items=[AddressSuggestionResponse.from_domain(item) for item in suggestions]
    )


@router.get("/resolve", response_model=ResolvedAddressResponse)
async def resolve_address(request: Request, id: UUID) -> ResolvedAddressResponse:
    address = await get_address_service(request).resolve(id)
    return ResolvedAddressResponse.from_domain(address)


@router.get(
    "/{address_id}/administrative-context",
    response_model=AdministrativeContextResponse,
)
async def resolve_administrative_context(
    request: Request,
    address_id: UUID,
) -> AdministrativeContextResponse:
    context = await get_administrative_context_service(request).resolve_for_address(
        address_id
    )
    return AdministrativeContextResponse.from_domain(context)


@router.get(
    "/{address_id}/neighborhood-indicators",
    response_model=NeighborhoodIndicatorsResponse,
)
async def resolve_neighborhood_indicators(
    request: Request,
    address_id: UUID,
) -> NeighborhoodIndicatorsResponse:
    result = await get_neighborhood_indicators_service(request).resolve_for_address(
        address_id
    )
    return NeighborhoodIndicatorsResponse.from_domain(result)
