from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import (
    SourceContractError,
    UnsupportedAddressableObjectError,
)
from woonlens.application.services.energy import EnergyRegistrationService
from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.energy import EnergyRegistration, EnergyRegistrationDetails

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
OBJECT_ID = "0599010000295420"
SOURCE = SourceMetadata("RVO", "EP", datetime.now(UTC), "Terms")


class DetailsStub:
    def __init__(self, object_type: str = "Verblijfsobject") -> None:
        self.object_type = object_type

    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        return ResolvedAddress(
            address_id,
            "number",
            OBJECT_ID,
            self.object_type,
            "Street",
            "1",
            None,
            None,
            "1234AB",
            "City",
            Coordinates(4.9, 52.37),
            SOURCE,
        )


def energy(bag_id: str) -> EnergyRegistration:
    return EnergyRegistration(
        bag_id,
        (),
        datetime(2026, 1, 1),
        None,
        datetime(2036, 1, 1),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "B",
        None,
        None,
        None,
        None,
        None,
    )


class EnergySpy:
    def __init__(self, returned_id: str = OBJECT_ID) -> None:
        self.returned_id = returned_id
        self.requested_id: str | None = None

    async def fetch(self, bag_object_id: str) -> EnergyRegistrationDetails:
        self.requested_id = bag_object_id
        return EnergyRegistrationDetails(energy(self.returned_id), SOURCE)


@pytest.mark.anyio
async def test_service_uses_trusted_bag_identifier() -> None:
    registrations = EnergySpy()
    result = await EnergyRegistrationService(
        DetailsStub(), registrations
    ).resolve_for_address(ADDRESS_ID)
    assert registrations.requested_id == OBJECT_ID
    assert result.registration.energy_class == "B"


@pytest.mark.anyio
async def test_service_rejects_unsupported_object_type() -> None:
    with pytest.raises(UnsupportedAddressableObjectError):
        await EnergyRegistrationService(
            DetailsStub("Ligplaats"), EnergySpy()
        ).resolve_for_address(ADDRESS_ID)


@pytest.mark.anyio
async def test_service_rejects_mismatched_result() -> None:
    with pytest.raises(SourceContractError):
        await EnergyRegistrationService(
            DetailsStub(), EnergySpy("1" * 16)
        ).resolve_for_address(ADDRESS_ID)
