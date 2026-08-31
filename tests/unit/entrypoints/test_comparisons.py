from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from woonlens.application.services.addresses import AddressService
from woonlens.application.services.comparison import LiveHomeComparisonService
from woonlens.bootstrap.settings import Settings
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.domain.overview import HomeOverview, UnavailableSection
from woonlens.entrypoints.api import create_app

FIRST = UUID("11111111-1111-4111-8111-111111111111")
SECOND = UUID("22222222-2222-4222-8222-222222222222")
SOURCE = SourceMetadata("Provider", "Dataset", datetime.now(UTC), "Terms")


class SearchFake:
    async def suggest(self, query: str, *, limit: int) -> tuple[AddressSuggestion, ...]:
        del query, limit
        return ()


class DetailsFake:
    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        raise AssertionError(address_id)


class OverviewFake:
    async def resolve(self, address_id: UUID) -> HomeOverview:
        address = ResolvedAddress(
            address_id,
            "0599200000508415",
            "0599010000295420",
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
        return HomeOverview(
            address,
            None,
            None,
            None,
            None,
            (
                UnavailableSection("property", "source_unavailable"),
                UnavailableSection("energy_registration", "source_configuration_error"),
                UnavailableSection("administrative_context", "source_unavailable"),
                UnavailableSection("neighborhood_indicators", "dependency_unavailable"),
            ),
        )


def create_test_app() -> FastAPI:
    return create_app(
        Settings(environment="test"),
        AddressService(SearchFake(), DetailsFake(), suggestion_limit=8),
        comparison_service=LiveHomeComparisonService(OverviewFake()),
    )


def test_endpoint_preserves_order_and_returns_metric_contract() -> None:
    with TestClient(create_test_app()) as client:
        response = client.post(
            "/api/v1/comparisons/live",
            json={"address_ids": [str(FIRST), str(SECOND)]},
        )
    assert response.status_code == 200
    body = response.json()
    assert [item["address_id"] for item in body["homes"]] == [str(FIRST), str(SECOND)]
    assert body["metrics"][0]["metric"]["key"] == "registered_area_m2"
    assert body["metrics"][0]["values"][0]["missing_reason"] == "source_unavailable"
    assert body["notices"][0]["code"] == "area_definition_difference"


def test_endpoint_rejects_count_and_duplicate_addresses() -> None:
    with TestClient(create_test_app()) as client:
        too_few = client.post(
            "/api/v1/comparisons/live", json={"address_ids": [str(FIRST)]}
        )
        duplicate = client.post(
            "/api/v1/comparisons/live",
            json={"address_ids": [str(FIRST), str(FIRST)]},
        )
    assert too_few.status_code == 422
    assert duplicate.status_code == 422
