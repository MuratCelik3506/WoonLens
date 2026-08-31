from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import (
    SourceContractError,
    UnsupportedAddressableObjectError,
)
from woonlens.application.services.property import PropertyDetailsService
from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.property import PropertyDetails, ResidentialUnit

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
OBJECT_ID = "0599010000295420"
SOURCE = SourceMetadata("PDOK", "BAG", datetime.now(UTC), "Public Domain Mark 1.0")


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


class PropertySpy:
    def __init__(self, returned_id: str = OBJECT_ID) -> None:
        self.returned_id = returned_id
        self.requested_id: str | None = None

    async def fetch(self, addressable_object_id: str) -> PropertyDetails:
        self.requested_id = addressable_object_id
        return PropertyDetails(
            ResidentialUnit(self.returned_id, None, (), None), (), SOURCE
        )


@pytest.mark.anyio
async def test_service_uses_trusted_resolved_bag_identifier() -> None:
    properties = PropertySpy()
    result = await PropertyDetailsService(
        DetailsStub(), properties
    ).resolve_for_address(ADDRESS_ID)

    assert properties.requested_id == OBJECT_ID
    assert result.residential_unit.id == OBJECT_ID


@pytest.mark.anyio
async def test_service_rejects_non_residential_addressable_object() -> None:
    with pytest.raises(UnsupportedAddressableObjectError):
        await PropertyDetailsService(
            DetailsStub("Standplaats"), PropertySpy()
        ).resolve_for_address(ADDRESS_ID)


@pytest.mark.anyio
async def test_service_rejects_mismatched_provider_result() -> None:
    with pytest.raises(SourceContractError):
        await PropertyDetailsService(
            DetailsStub(), PropertySpy("0" * 16)
        ).resolve_for_address(ADDRESS_ID)
