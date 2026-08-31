from uuid import UUID

from woonlens.application.errors import (
    SourceContractError,
    UnsupportedAddressableObjectError,
)
from woonlens.application.ports.addresses import AddressDetailsPort
from woonlens.application.ports.energy import EnergyRegistrationPort
from woonlens.domain.energy import EnergyRegistrationDetails


class EnergyRegistrationService:
    """Resolve an address before requesting its current energy registration."""

    def __init__(
        self,
        addresses: AddressDetailsPort,
        registrations: EnergyRegistrationPort,
    ) -> None:
        self._addresses = addresses
        self._registrations = registrations

    async def resolve_for_address(self, address_id: UUID) -> EnergyRegistrationDetails:
        address = await self._addresses.resolve(address_id)
        if address.addressable_object_type != "Verblijfsobject":
            raise UnsupportedAddressableObjectError
        result = await self._registrations.fetch(address.addressable_object_id)
        if result.registration.bag_object_id != address.addressable_object_id:
            raise SourceContractError
        return result
