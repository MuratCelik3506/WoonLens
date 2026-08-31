from datetime import datetime
from typing import Annotated, Self, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from woonlens.application.services.addresses import AddressService
from woonlens.application.services.administrative import AdministrativeContextService
from woonlens.application.services.energy import EnergyRegistrationService
from woonlens.application.services.indicators import NeighborhoodIndicatorsService
from woonlens.application.services.overview import HomeOverviewService
from woonlens.application.services.property import PropertyDetailsService
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.domain.energy import EnergyRegistration, EnergyRegistrationDetails
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators
from woonlens.domain.overview import HomeOverview, UnavailableSection
from woonlens.domain.property import Building, PropertyDetails, ResidentialUnit

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


class ResidentialUnitResponse(BaseModel):
    id: str
    status: str | None
    use_purposes: list[str]
    registered_area_m2: int | None
    area_definition: str = "BAG registered area"

    @classmethod
    def from_domain(cls, unit: ResidentialUnit) -> Self:
        return cls(
            id=unit.id,
            status=unit.status,
            use_purposes=list(unit.use_purposes),
            registered_area_m2=unit.registered_area_m2,
        )


class BuildingResponse(BaseModel):
    id: str
    status: str | None
    construction_year: int | None
    use_purposes: list[str]
    residential_unit_count: int | None

    @classmethod
    def from_domain(cls, building: Building) -> Self:
        return cls(
            id=building.id,
            status=building.status,
            construction_year=building.construction_year,
            use_purposes=list(building.use_purposes),
            residential_unit_count=building.residential_unit_count,
        )


class PropertyDetailsResponse(BaseModel):
    residential_unit: ResidentialUnitResponse
    buildings: list[BuildingResponse]
    source: SourceResponse

    @classmethod
    def from_domain(cls, details: PropertyDetails) -> Self:
        return cls(
            residential_unit=ResidentialUnitResponse.from_domain(
                details.residential_unit
            ),
            buildings=[
                BuildingResponse.from_domain(building) for building in details.buildings
            ],
            source=SourceResponse.from_domain(details.source),
        )


class EnergyRegistrationResponse(BaseModel):
    bag_object_id: str
    bag_building_ids: list[str]
    registration_date: datetime
    inspection_date: datetime | None
    valid_until: datetime
    assessment_type: str | None
    registration_status: str | None
    building_class: str | None
    building_type: str | None
    building_subtype: str | None
    construction_year: int | None
    thermal_zone_area_m2: float | None
    area_definition: str = "EP-Online thermal-zone area"
    energy_class: str | None
    energy_demand_kwh_m2_year: float | None
    primary_fossil_energy_kwh_m2_year: float | None
    renewable_energy_share_pct: float | None
    calculated_co2_kg_m2_year: float | None
    calculated_energy_use_kwh_m2_year: float | None

    @classmethod
    def from_domain(cls, registration: EnergyRegistration) -> Self:
        return cls(
            bag_object_id=registration.bag_object_id,
            bag_building_ids=list(registration.bag_building_ids),
            registration_date=registration.registration_date,
            inspection_date=registration.inspection_date,
            valid_until=registration.valid_until,
            assessment_type=registration.assessment_type,
            registration_status=registration.registration_status,
            building_class=registration.building_class,
            building_type=registration.building_type,
            building_subtype=registration.building_subtype,
            construction_year=registration.construction_year,
            thermal_zone_area_m2=registration.thermal_zone_area_m2,
            energy_class=registration.energy_class,
            energy_demand_kwh_m2_year=registration.energy_demand_kwh_m2_year,
            primary_fossil_energy_kwh_m2_year=(
                registration.primary_fossil_energy_kwh_m2_year
            ),
            renewable_energy_share_pct=registration.renewable_energy_share_pct,
            calculated_co2_kg_m2_year=registration.calculated_co2_kg_m2_year,
            calculated_energy_use_kwh_m2_year=(
                registration.calculated_energy_use_kwh_m2_year
            ),
        )


class EnergyRegistrationDetailsResponse(BaseModel):
    registration: EnergyRegistrationResponse
    source: SourceResponse

    @classmethod
    def from_domain(cls, details: EnergyRegistrationDetails) -> Self:
        return cls(
            registration=EnergyRegistrationResponse.from_domain(details.registration),
            source=SourceResponse.from_domain(details.source),
        )


class UnavailableSectionResponse(BaseModel):
    section: str
    reason: str

    @classmethod
    def from_domain(cls, item: UnavailableSection) -> Self:
        return cls(section=item.section, reason=item.reason)


class HomeOverviewResponse(BaseModel):
    address: ResolvedAddressResponse
    property: PropertyDetailsResponse | None
    energy_registration: EnergyRegistrationDetailsResponse | None
    administrative_context: AdministrativeContextResponse | None
    neighborhood_indicators: NeighborhoodIndicatorsResponse | None
    unavailable_sections: list[UnavailableSectionResponse]

    @classmethod
    def from_domain(cls, overview: HomeOverview) -> Self:
        return cls(
            address=ResolvedAddressResponse.from_domain(overview.address),
            property=(
                PropertyDetailsResponse.from_domain(overview.property)
                if overview.property is not None
                else None
            ),
            energy_registration=(
                EnergyRegistrationDetailsResponse.from_domain(
                    overview.energy_registration
                )
                if overview.energy_registration is not None
                else None
            ),
            administrative_context=(
                AdministrativeContextResponse.from_domain(
                    overview.administrative_context
                )
                if overview.administrative_context is not None
                else None
            ),
            neighborhood_indicators=(
                NeighborhoodIndicatorsResponse.from_domain(
                    overview.neighborhood_indicators
                )
                if overview.neighborhood_indicators is not None
                else None
            ),
            unavailable_sections=[
                UnavailableSectionResponse.from_domain(item)
                for item in overview.unavailable_sections
            ],
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


def get_property_details_service(request: Request) -> PropertyDetailsService:
    return cast(PropertyDetailsService, request.app.state.property_details_service)


def get_energy_registration_service(request: Request) -> EnergyRegistrationService:
    return cast(
        EnergyRegistrationService, request.app.state.energy_registration_service
    )


def get_home_overview_service(request: Request) -> HomeOverviewService:
    return cast(HomeOverviewService, request.app.state.home_overview_service)


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


@router.get("/{address_id}/property", response_model=PropertyDetailsResponse)
async def resolve_property_details(
    request: Request,
    address_id: UUID,
) -> PropertyDetailsResponse:
    details = await get_property_details_service(request).resolve_for_address(
        address_id
    )
    return PropertyDetailsResponse.from_domain(details)


@router.get(
    "/{address_id}/energy-registration",
    response_model=EnergyRegistrationDetailsResponse,
)
async def resolve_energy_registration(
    request: Request,
    address_id: UUID,
) -> EnergyRegistrationDetailsResponse:
    details = await get_energy_registration_service(request).resolve_for_address(
        address_id
    )
    return EnergyRegistrationDetailsResponse.from_domain(details)


@router.get("/{address_id}/overview", response_model=HomeOverviewResponse)
async def resolve_home_overview(
    request: Request,
    address_id: UUID,
) -> HomeOverviewResponse:
    overview = await get_home_overview_service(request).resolve(address_id)
    return HomeOverviewResponse.from_domain(overview)
