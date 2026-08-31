import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import AddressNotFoundError, SourceUnavailableError
from woonlens.application.services.comparison import LiveHomeComparisonService
from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.domain.energy import EnergyRegistration, EnergyRegistrationDetails
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators
from woonlens.domain.overview import HomeOverview, UnavailableSection
from woonlens.domain.property import Building, PropertyDetails, ResidentialUnit

FIRST = UUID("11111111-1111-4111-8111-111111111111")
SECOND = UUID("22222222-2222-4222-8222-222222222222")
SOURCE = SourceMetadata("Provider", "Dataset", datetime.now(UTC), "Terms")


def overview(
    address_id: UUID, area: int, energy_class: str, woz: float
) -> HomeOverview:
    bag_id = "0599010000295420" if address_id == FIRST else "0599010000295421"
    address = ResolvedAddress(
        address_id,
        "0599200000508415",
        bag_id,
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
    property_details = PropertyDetails(
        ResidentialUnit(bag_id, None, (), area),
        (Building("0599100000691863", None, 1900 + area, (), 1),),
        SOURCE,
    )
    energy = EnergyRegistrationDetails(
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
            float(area - 5),
            energy_class,
            100.0 + area,
            150.0 + area,
            20.0,
            None,
            None,
        ),
        SOURCE,
    )
    neighborhood = AdministrativeArea("BU05990112", "Cool")
    context = AdministrativeContext(neighborhood, None, None, None, (SOURCE,))
    indicators = NeighborhoodIndicators(
        neighborhood,
        "85984NED",
        2024,
        (NeighborhoodIndicator("average_woz_value", "M1", "WOZ", woz, "EUR", "EUR"),),
        SOURCE,
    )
    return HomeOverview(address, property_details, energy, context, indicators, ())


class OverviewStub:
    def __init__(
        self,
        results: dict[UUID, HomeOverview | Exception],
        concurrent: bool = False,
    ) -> None:
        self.results = results
        self.concurrent = concurrent
        self.started = 0
        self.gate = asyncio.Event()

    async def resolve(self, address_id: UUID) -> HomeOverview:
        if self.concurrent:
            self.started += 1
            if self.started == len(self.results):
                self.gate.set()
            await asyncio.wait_for(self.gate.wait(), timeout=1)
        result = self.results[address_id]
        if isinstance(result, Exception):
            raise result
        return result


@pytest.mark.anyio
async def test_compares_in_input_order_concurrently_and_calculates_deltas() -> None:
    overviews = OverviewStub(
        {
            FIRST: overview(FIRST, 60, "B", 300000),
            SECOND: overview(SECOND, 75, "A", 350000),
        },
        concurrent=True,
    )
    result = await LiveHomeComparisonService(overviews).compare((FIRST, SECOND))

    assert overviews.started == 2
    assert [home.address_id for home in result.homes] == [FIRST, SECOND]
    area = next(
        item for item in result.metrics if item.metric.key == "registered_area_m2"
    )
    assert [value.value for value in area.values] == [60, 75]
    assert [value.delta_from_baseline for value in area.values] == [0, 15]
    energy_class = next(
        item for item in result.metrics if item.metric.key == "energy_class"
    )
    assert all(value.delta_from_baseline is None for value in energy_class.values)
    woz = next(
        item for item in result.metrics if item.metric.key == "average_woz_value"
    )
    assert woz.values[1].delta_from_baseline == 50000


@pytest.mark.anyio
async def test_isolates_expected_unavailable_home() -> None:
    result = await LiveHomeComparisonService(
        OverviewStub(
            {FIRST: AddressNotFoundError(), SECOND: overview(SECOND, 75, "A", 350000)}
        )
    ).compare((FIRST, SECOND))

    assert result.homes[0].unavailable_reason == "address_not_found"
    area = next(
        item for item in result.metrics if item.metric.key == "registered_area_m2"
    )
    assert area.values[0].missing_reason == "address_not_found"
    assert area.values[1].is_baseline is True
    assert area.values[1].delta_from_baseline == 0


@pytest.mark.anyio
async def test_preserves_section_missing_reason() -> None:
    second = overview(SECOND, 75, "A", 350000)
    second = HomeOverview(
        second.address,
        second.property,
        None,
        second.administrative_context,
        second.neighborhood_indicators,
        (UnavailableSection("energy_registration", SourceUnavailableError.code),),
    )
    result = await LiveHomeComparisonService(
        OverviewStub({FIRST: overview(FIRST, 60, "B", 300000), SECOND: second})
    ).compare((FIRST, SECOND))
    energy = next(item for item in result.metrics if item.metric.key == "energy_class")
    assert energy.values[1].missing_reason == "source_unavailable"


@pytest.mark.anyio
async def test_does_not_hide_unexpected_error() -> None:
    with pytest.raises(RuntimeError, match="bug"):
        await LiveHomeComparisonService(
            OverviewStub(
                {FIRST: RuntimeError("bug"), SECOND: overview(SECOND, 75, "A", 350000)}
            )
        ).compare((FIRST, SECOND))


@pytest.mark.anyio
async def test_rejects_invalid_direct_input() -> None:
    with pytest.raises(ValueError):
        await LiveHomeComparisonService(OverviewStub({})).compare((FIRST, FIRST))
