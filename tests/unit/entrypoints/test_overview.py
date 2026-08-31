from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from woonlens.application.services.addresses import AddressService
from woonlens.application.services.overview import HomeOverviewService
from woonlens.bootstrap.settings import Settings
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.domain.energy import EnergyRegistrationDetails
from woonlens.domain.indicators import NeighborhoodIndicators
from woonlens.domain.property import PropertyDetails, ResidentialUnit
from woonlens.entrypoints.api import create_app

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
OBJECT_ID = "0599010000295420"
SOURCE = SourceMetadata("PDOK", "Dataset", datetime(2026, 8, 31, tzinfo=UTC), "Terms")


class SearchFake:
    async def suggest(self, query: str, *, limit: int) -> tuple[AddressSuggestion, ...]:
        del query, limit
        return ()


class DetailsFake:
    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        return ResolvedAddress(
            address_id,
            "number",
            OBJECT_ID,
            "Verblijfsobject",
            "Street",
            "1",
            None,
            None,
            "1234AB",
            "City",
            Coordinates(4.9, 52.37),
            SOURCE,
        )


class PropertyFake:
    async def fetch(self, bag_id: str) -> PropertyDetails:
        return PropertyDetails(ResidentialUnit(bag_id, None, (), 62), (), SOURCE)


class EnergyMissingFake:
    async def fetch(self, bag_id: str) -> EnergyRegistrationDetails:
        from woonlens.application.errors import SourceConfigurationError

        del bag_id
        raise SourceConfigurationError


class ContextFake:
    async def resolve(self, coordinates: Coordinates) -> AdministrativeContext:
        del coordinates
        return AdministrativeContext(
            AdministrativeArea("BU05990112", "Cool"), None, None, None, (SOURCE,)
        )


class IndicatorsFake:
    async def fetch(self, code: str) -> NeighborhoodIndicators:
        from woonlens.application.errors import SourceUnavailableError

        del code
        raise SourceUnavailableError


def create_test_app() -> FastAPI:
    details = DetailsFake()
    overview = HomeOverviewService(
        details, PropertyFake(), EnergyMissingFake(), ContextFake(), IndicatorsFake()
    )
    return create_app(
        Settings(environment="test"),
        AddressService(SearchFake(), details, suggestion_limit=8),
        home_overview_service=overview,
    )


def test_endpoint_returns_partial_overview_with_safe_reasons() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get(f"/api/v1/addresses/{ADDRESS_ID}/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["address"]["addressable_object_id"] == OBJECT_ID
    assert body["property"]["residential_unit"]["registered_area_m2"] == 62
    assert body["energy_registration"] is None
    assert body["administrative_context"]["neighborhood"]["name"] == "Cool"
    assert body["neighborhood_indicators"] is None
    assert body["unavailable_sections"] == [
        {"section": "energy_registration", "reason": "source_configuration_error"},
        {"section": "neighborhood_indicators", "reason": "source_unavailable"},
    ]


def test_endpoint_rejects_non_uuid_address() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/api/v1/addresses/not-a-uuid/overview")
    assert response.status_code == 422
