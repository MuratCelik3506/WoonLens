from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import NeighborhoodContextNotFoundError
from woonlens.application.services.indicators import NeighborhoodIndicatorsService
from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
SOURCE = SourceMetadata("CBS", "Synthetic", datetime.now(UTC), "CC BY 4.0")


class DetailsStub:
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


class ContextStub:
    def __init__(self, neighborhood: AdministrativeArea | None) -> None:
        self.neighborhood = neighborhood

    async def resolve(self, coordinates: Coordinates) -> AdministrativeContext:
        assert coordinates == Coordinates(4.9, 52.37)
        return AdministrativeContext(
            self.neighborhood,
            None,
            None,
            AdministrativeArea("PV28", "Zuid-Holland"),
            (SOURCE,),
        )


class IndicatorsSpy:
    code: str | None = None

    async def fetch(self, neighborhood_code: str) -> NeighborhoodIndicators:
        self.code = neighborhood_code
        return NeighborhoodIndicators(
            AdministrativeArea(neighborhood_code, neighborhood_code),
            "85984NED",
            2024,
            (
                NeighborhoodIndicator(
                    "average_woz_value",
                    "M001642",
                    "Average WOZ",
                    372000.0,
                    "EUR",
                    "x 1 000 euro",
                ),
            ),
            SOURCE,
        )


@pytest.mark.anyio
async def test_service_uses_trusted_context_and_restores_neighborhood_name() -> None:
    neighborhood = AdministrativeArea("BU05990112", "Cool")
    indicators = IndicatorsSpy()
    result = await NeighborhoodIndicatorsService(
        DetailsStub(), ContextStub(neighborhood), indicators
    ).resolve_for_address(ADDRESS_ID)

    assert indicators.code == "BU05990112"
    assert result.neighborhood == neighborhood


@pytest.mark.anyio
async def test_service_rejects_missing_neighborhood_context() -> None:
    with pytest.raises(NeighborhoodContextNotFoundError):
        await NeighborhoodIndicatorsService(
            DetailsStub(), ContextStub(None), IndicatorsSpy()
        ).resolve_for_address(ADDRESS_ID)
