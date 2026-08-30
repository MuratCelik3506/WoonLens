from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from woonlens.application.errors import (
    AddressNotFoundError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.application.services.addresses import AddressService
from woonlens.bootstrap.settings import Settings
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.entrypoints.api import create_app

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
SOURCE = SourceMetadata("PDOK", "Synthetic source", NOW, "CC BY 4.0")


class SearchFake:
    error: Exception | None = None

    async def suggest(self, query: str, *, limit: int) -> tuple[AddressSuggestion, ...]:
        del query, limit
        if self.error is not None:
            raise self.error
        return (
            AddressSuggestion(
                ADDRESS_ID,
                "Examplelaan 10, 1234AB Teststad",
                Coordinates(4.9, 52.3),
                SOURCE,
            ),
        )


class DetailsFake:
    error: Exception | None = None

    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        if self.error is not None:
            raise self.error
        return ResolvedAddress(
            address_id,
            "0000200000000001",
            "0000010000000001",
            "Verblijfsobject",
            "Examplelaan",
            "10",
            None,
            "A",
            "1234AB",
            "Teststad",
            Coordinates(4.9, 52.3),
            SOURCE,
        )


def test_suggest_endpoint_returns_owned_public_schema() -> None:
    service = AddressService(SearchFake(), DetailsFake(), suggestion_limit=8)
    app = create_app(Settings(environment="test"), service)

    with TestClient(app) as client:
        response = client.get("/api/v1/addresses/suggest", params={"q": "Example"})

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["id"] == str(ADDRESS_ID)
    assert body["items"][0]["coordinates"]["crs"].endswith("CRS84")
    assert body["items"][0]["source"]["license"] == "CC BY 4.0"
    assert "href" not in body["items"][0]


@pytest.mark.parametrize("query", ["", "x", "x" * 201])
def test_suggest_endpoint_rejects_invalid_query(query: str) -> None:
    service = AddressService(SearchFake(), DetailsFake(), suggestion_limit=8)
    app = create_app(Settings(environment="test"), service)

    with TestClient(app) as client:
        response = client.get("/api/v1/addresses/suggest", params={"q": query})

    assert response.status_code == 422


def test_resolve_endpoint_returns_official_join_identifiers() -> None:
    service = AddressService(SearchFake(), DetailsFake(), suggestion_limit=8)
    app = create_app(Settings(environment="test"), service)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/addresses/resolve", params={"id": str(ADDRESS_ID)}
        )

    assert response.status_code == 200
    assert response.json()["number_designation_id"] == "0000200000000001"
    assert response.json()["addressable_object_id"] == "0000010000000001"


def test_resolve_endpoint_rejects_non_uuid_id() -> None:
    service = AddressService(SearchFake(), DetailsFake(), suggestion_limit=8)
    app = create_app(Settings(environment="test"), service)

    with TestClient(app) as client:
        response = client.get("/api/v1/addresses/resolve", params={"id": "unsafe"})

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (AddressNotFoundError(), 404),
        (SourceRateLimitedError(), 503),
        (SourceUnavailableError(), 503),
        (SourceContractError(), 502),
    ],
)
def test_typed_errors_return_safe_problem_details(
    error: Exception, status: int
) -> None:
    details = DetailsFake()
    details.error = error
    service = AddressService(SearchFake(), details, suggestion_limit=8)
    app = create_app(Settings(environment="test"), service)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/api/v1/addresses/resolve", params={"id": str(ADDRESS_ID)}
        )

    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "provider.test" not in response.text
