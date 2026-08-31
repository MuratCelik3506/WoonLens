from datetime import UTC, datetime
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from woonlens.application.services.addresses import AddressService
from woonlens.application.services.energy import EnergyRegistrationService
from woonlens.bootstrap.settings import Settings
from woonlens.domain.addresses import (
    AddressSuggestion,
    Coordinates,
    ResolvedAddress,
    SourceMetadata,
)
from woonlens.domain.energy import EnergyRegistration, EnergyRegistrationDetails
from woonlens.entrypoints.api import create_app

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
OBJECT_ID = "0599010000295420"
SOURCE = SourceMetadata(
    "RVO / EP-Online",
    "EP-Online",
    datetime(2026, 8, 31, tzinfo=UTC),
    "EP-Online Terms of Use",
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


class EnergyFake:
    async def fetch(self, bag_object_id: str) -> EnergyRegistrationDetails:
        return EnergyRegistrationDetails(
            EnergyRegistration(
                bag_object_id,
                ("0599100000691863",),
                datetime(2026, 2, 4),
                datetime(2026, 1, 14),
                datetime(2036, 1, 14),
                "Basisopname",
                "Bestaand",
                "Woningbouw",
                "Appartement",
                "Tussenmidden",
                1873,
                54.41,
                "B",
                109.02,
                172.52,
                0.0,
                31.8,
                172.51,
            ),
            SOURCE,
        )


def create_test_app() -> FastAPI:
    details = DetailsFake()
    return create_app(
        Settings(environment="test"),
        AddressService(SearchFake(), details, suggestion_limit=8),
        energy_registration_service=EnergyRegistrationService(details, EnergyFake()),
    )


def test_endpoint_returns_labeled_energy_registration() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get(f"/api/v1/addresses/{ADDRESS_ID}/energy-registration")
    assert response.status_code == 200
    body = response.json()
    assert body["registration"]["energy_class"] == "B"
    assert body["registration"]["thermal_zone_area_m2"] == 54.41
    assert body["registration"]["area_definition"] == "EP-Online thermal-zone area"
    assert body["source"]["license"] == "EP-Online Terms of Use"


def test_endpoint_rejects_non_uuid_address() -> None:
    with TestClient(create_test_app()) as client:
        response = client.get("/api/v1/addresses/not-a-uuid/energy-registration")
    assert response.status_code == 422
