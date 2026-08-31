import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import (
    EnergyRegistrationNotFoundError,
    SourceConfigurationError,
    SourceUnavailableError,
)
from woonlens.application.services.overview import HomeOverviewService
from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.domain.energy import EnergyRegistration, EnergyRegistrationDetails
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators
from woonlens.domain.property import PropertyDetails, ResidentialUnit

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
OBJECT_ID = "0599010000295420"
SOURCE = SourceMetadata("Provider", "Dataset", datetime.now(UTC), "Terms")
NEIGHBORHOOD = AdministrativeArea("BU05990112", "Cool")


class AddressSpy:
    calls = 0

    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        self.calls += 1
        return ResolvedAddress(
            address_id,
            "0599200000508415",
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


class StartBarrier:
    def __init__(self) -> None:
        self.started = 0
        self.event = asyncio.Event()

    async def wait(self) -> None:
        self.started += 1
        if self.started == 3:
            self.event.set()
        await asyncio.wait_for(self.event.wait(), timeout=1)


class PropertyStub:
    def __init__(self, barrier: StartBarrier | None = None) -> None:
        self.barrier = barrier
        self.requested: str | None = None

    async def fetch(self, bag_id: str) -> PropertyDetails:
        self.requested = bag_id
        if self.barrier:
            await self.barrier.wait()
        return PropertyDetails(ResidentialUnit(bag_id, None, (), 62), (), SOURCE)


class EnergyStub:
    def __init__(
        self,
        barrier: StartBarrier | None = None,
        error: Exception | None = None,
    ) -> None:
        self.barrier = barrier
        self.error = error
        self.requested: str | None = None

    async def fetch(self, bag_id: str) -> EnergyRegistrationDetails:
        self.requested = bag_id
        if self.barrier:
            await self.barrier.wait()
        if self.error:
            raise self.error
        return EnergyRegistrationDetails(
            EnergyRegistration(
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
            ),
            SOURCE,
        )


class ContextStub:
    def __init__(
        self,
        barrier: StartBarrier | None = None,
        error: Exception | None = None,
    ) -> None:
        self.barrier = barrier
        self.error = error
        self.coordinates: Coordinates | None = None

    async def resolve(self, coordinates: Coordinates) -> AdministrativeContext:
        self.coordinates = coordinates
        if self.barrier:
            await self.barrier.wait()
        if self.error:
            raise self.error
        return AdministrativeContext(NEIGHBORHOOD, None, None, None, (SOURCE,))


class IndicatorsStub:
    requested: str | None = None

    async def fetch(self, code: str) -> NeighborhoodIndicators:
        self.requested = code
        return NeighborhoodIndicators(
            NEIGHBORHOOD,
            "85984NED",
            2024,
            (NeighborhoodIndicator("woz", "M1", "WOZ", 1.0, "EUR", "EUR"),),
            SOURCE,
        )


@pytest.mark.anyio
async def test_composes_trusted_sources_and_starts_independent_work_concurrently() -> (
    None
):
    addresses = AddressSpy()
    barrier = StartBarrier()
    properties = PropertyStub(barrier)
    energy = EnergyStub(barrier)
    context = ContextStub(barrier)
    indicators = IndicatorsStub()

    result = await HomeOverviewService(
        addresses, properties, energy, context, indicators
    ).resolve(ADDRESS_ID)

    assert addresses.calls == 1
    assert barrier.started == 3
    assert properties.requested == OBJECT_ID
    assert energy.requested == OBJECT_ID
    assert context.coordinates == Coordinates(4.9, 52.37)
    assert indicators.requested == NEIGHBORHOOD.code
    assert result.unavailable_sections == ()


@pytest.mark.anyio
async def test_keeps_successful_sections_when_optional_source_fails() -> None:
    result = await HomeOverviewService(
        AddressSpy(),
        PropertyStub(),
        EnergyStub(error=SourceConfigurationError()),
        ContextStub(),
        IndicatorsStub(),
    ).resolve(ADDRESS_ID)

    assert result.property is not None
    assert result.energy_registration is None
    assert result.neighborhood_indicators is not None
    assert result.unavailable_sections[0].section == "energy_registration"
    assert result.unavailable_sections[0].reason == "source_configuration_error"


@pytest.mark.anyio
async def test_context_failure_marks_dependent_indicators_unavailable() -> None:
    result = await HomeOverviewService(
        AddressSpy(),
        PropertyStub(),
        EnergyStub(error=EnergyRegistrationNotFoundError()),
        ContextStub(error=SourceUnavailableError()),
        IndicatorsStub(),
    ).resolve(ADDRESS_ID)

    failures = {item.section: item.reason for item in result.unavailable_sections}
    assert failures == {
        "energy_registration": "energy_registration_not_found",
        "administrative_context": "source_unavailable",
        "neighborhood_indicators": "dependency_unavailable",
    }


@pytest.mark.anyio
async def test_does_not_hide_unexpected_programming_errors() -> None:
    with pytest.raises(RuntimeError, match="bug"):
        await HomeOverviewService(
            AddressSpy(),
            PropertyStub(),
            EnergyStub(error=RuntimeError("bug")),
            ContextStub(),
            IndicatorsStub(),
        ).resolve(ADDRESS_ID)
