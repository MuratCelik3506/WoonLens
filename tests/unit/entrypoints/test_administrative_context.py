from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from woonlens.application.services.addresses import AddressService
from woonlens.application.services.administrative import AdministrativeContextService
from woonlens.bootstrap.settings import Settings
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.entrypoints.api import create_app

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
SOURCE = SourceMetadata(
    "PDOK",
    "CBS Wijken en Buurten 2026",
    datetime(2026, 8, 30, 12, 0, tzinfo=UTC),
    "CC BY 4.0",
)


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
        assert coordinates == Coordinates(4.9, 52.37)
        return AdministrativeContext(
            AdministrativeArea("BU0363AF08", "Zuiderkerkbuurt"),
            AdministrativeArea("WK0363AF", "Nieuwmarkt/Lastage"),
            AdministrativeArea("GM0363", "Amsterdam"),
            AdministrativeArea("PV27", "Noord-Holland"),
            (SOURCE,),
        )


def test_administrative_context_endpoint_returns_owned_schema() -> None:
    details = DetailsFake()
    addresses = AddressService(SearchFake(), details, suggestion_limit=8)
    context = AdministrativeContextService(details, ContextFake())
    app = create_app(Settings(environment="test"), addresses, context)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/addresses/{ADDRESS_ID}/administrative-context")

    assert response.status_code == 200
    body = response.json()
    assert body["neighborhood"] == {
        "code": "BU0363AF08",
        "name": "Zuiderkerkbuurt",
    }
    assert body["municipality"]["name"] == "Amsterdam"
    assert body["province"]["code"] == "PV27"
    assert body["sources"][0]["license"] == "CC BY 4.0"


def test_administrative_context_endpoint_rejects_non_uuid_address() -> None:
    details = DetailsFake()
    app = create_app(
        Settings(environment="test"),
        AddressService(SearchFake(), details, suggestion_limit=8),
        AdministrativeContextService(details, ContextFake()),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/addresses/not-a-uuid/administrative-context")

    assert response.status_code == 422
