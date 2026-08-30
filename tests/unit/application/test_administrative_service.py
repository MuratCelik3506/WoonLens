from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.services.administrative import AdministrativeContextService
from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
SOURCE = SourceMetadata("PDOK", "Synthetic", datetime.now(UTC), "CC BY 4.0")


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


class ContextSpy:
    coordinates: Coordinates | None = None

    async def resolve(self, coordinates: Coordinates) -> AdministrativeContext:
        self.coordinates = coordinates
        return AdministrativeContext(
            None,
            None,
            None,
            AdministrativeArea("PV27", "Noord-Holland"),
            (SOURCE,),
        )


@pytest.mark.anyio
async def test_service_uses_coordinates_from_official_address_resolution() -> None:
    context = ContextSpy()
    result = await AdministrativeContextService(
        DetailsStub(), context
    ).resolve_for_address(ADDRESS_ID)

    assert context.coordinates == Coordinates(4.9, 52.37)
    assert result.province == AdministrativeArea("PV27", "Noord-Holland")
