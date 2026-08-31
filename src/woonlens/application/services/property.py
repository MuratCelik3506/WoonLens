from uuid import UUID

from woonlens.application.errors import (
    SourceContractError,
    UnsupportedAddressableObjectError,
)
from woonlens.application.ports.addresses import AddressDetailsPort
from woonlens.application.ports.property import PropertyDetailsPort
from woonlens.domain.property import PropertyDetails


class PropertyDetailsService:
    """Join a trusted BAG address to its live property and building facts."""

    def __init__(
        self,
        addresses: AddressDetailsPort,
        properties: PropertyDetailsPort,
    ) -> None:
        self._addresses = addresses
        self._properties = properties

    async def resolve_for_address(self, address_id: UUID) -> PropertyDetails:
        address = await self._addresses.resolve(address_id)
        if address.addressable_object_type != "Verblijfsobject":
            raise UnsupportedAddressableObjectError
        result = await self._properties.fetch(address.addressable_object_id)
        if result.residential_unit.id != address.addressable_object_id:
            raise SourceContractError
        return result
