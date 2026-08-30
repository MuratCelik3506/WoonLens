from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from woonlens.application.services.addresses import AddressService
from woonlens.application.services.administrative import AdministrativeContextService
from woonlens.application.services.indicators import NeighborhoodIndicatorsService
from woonlens.bootstrap.settings import Settings
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators
from woonlens.entrypoints.api import create_app

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
SOURCE = SourceMetadata(
    "Statistics Netherlands (CBS)",
    "Kerncijfers wijken en buurten 2024",
    datetime(2026, 8, 30, 12, 0, tzinfo=UTC),
    "CC BY 4.0",
)
NEIGHBORHOOD = AdministrativeArea("BU05990112", "Cool")


class SearchFake:
    async def suggest(self, query: str, *, limit: int) -> tuple[AddressSuggestion, ...]:
        del query, limit
        return ()


class DetailsFake:
    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        return ResolvedAddress(
            address_id,
            "number",
            "object",
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


class ContextFake:
    async def resolve(self, coordinates: Coordinates) -> AdministrativeContext:
        del coordinates
        return AdministrativeContext(
            NEIGHBORHOOD,
            None,
            None,
            AdministrativeArea("PV28", "Zuid-Holland"),
            (SOURCE,),
        )


class IndicatorsFake:
    async def fetch(self, neighborhood_code: str) -> NeighborhoodIndicators:
        assert neighborhood_code == NEIGHBORHOOD.code
        return NeighborhoodIndicators(
            AdministrativeArea(neighborhood_code, neighborhood_code),
            "85984NED",
            2024,
            (
                NeighborhoodIndicator(
                    "average_woz_value",
                    "M001642",
                    "Gemiddelde WOZ-waarde van woningen",
                    372000.0,
                    "EUR",
                    "x 1 000 euro",
                ),
                NeighborhoodIndicator(
                    "homes_with_solar_power",
                    "M008297",
                    "Woningen met zonnestroom",
                    None,
                    "%",
                    "%",
                    "not_published",
                ),
            ),
            SOURCE,
        )


def create_test_app() -> FastAPI:
    details = DetailsFake()
    context = ContextFake()
    addresses = AddressService(SearchFake(), details, suggestion_limit=8)
    administrative = AdministrativeContextService(details, context)
    indicators = NeighborhoodIndicatorsService(details, context, IndicatorsFake())
    return create_app(
        Settings(environment="test"), addresses, administrative, indicators
    )


def test_endpoint_labels_neighborhood_values_and_missing_state() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get(f"/api/v1/addresses/{ADDRESS_ID}/neighborhood-indicators")

    assert response.status_code == 200
    body = response.json()
    assert body["level"] == "neighborhood"
    assert body["neighborhood"] == {"code": "BU05990112", "name": "Cool"}
    assert body["dataset_id"] == "85984NED"
    assert body["dataset_year"] == 2024
    assert body["indicators"][0]["value"] == 372000.0
    assert body["indicators"][0]["unit"] == "EUR"
    assert body["indicators"][1]["value"] is None
    assert body["indicators"][1]["missing_reason"] == "not_published"
    assert body["source"]["license"] == "CC BY 4.0"


def test_endpoint_rejects_non_uuid_address() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/api/v1/addresses/not-a-uuid/neighborhood-indicators")

    assert response.status_code == 422
