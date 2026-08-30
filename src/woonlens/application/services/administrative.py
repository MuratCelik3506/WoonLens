from uuid import UUID

from woonlens.application.ports.addresses import AddressDetailsPort
from woonlens.application.ports.administrative import AdministrativeContextPort
from woonlens.domain.administrative import AdministrativeContext


class AdministrativeContextService:
    """Resolve a trusted BAG address before joining live administrative context."""

    def __init__(
        self,
        addresses: AddressDetailsPort,
        context: AdministrativeContextPort,
    ) -> None:
        self._addresses = addresses
        self._context = context

    async def resolve_for_address(self, address_id: UUID) -> AdministrativeContext:
        address = await self._addresses.resolve(address_id)
        return await self._context.resolve(address.coordinates)
