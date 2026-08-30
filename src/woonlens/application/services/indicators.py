from dataclasses import replace
from uuid import UUID

from woonlens.application.errors import NeighborhoodContextNotFoundError
from woonlens.application.ports.addresses import AddressDetailsPort
from woonlens.application.ports.administrative import AdministrativeContextPort
from woonlens.application.ports.indicators import NeighborhoodIndicatorsPort
from woonlens.domain.indicators import NeighborhoodIndicators


class NeighborhoodIndicatorsService:
    """Join one trusted BAG address to live neighbourhood indicators."""

    def __init__(
        self,
        addresses: AddressDetailsPort,
        administrative_context: AdministrativeContextPort,
        indicators: NeighborhoodIndicatorsPort,
    ) -> None:
        self._addresses = addresses
        self._administrative_context = administrative_context
        self._indicators = indicators

    async def resolve_for_address(self, address_id: UUID) -> NeighborhoodIndicators:
        address = await self._addresses.resolve(address_id)
        context = await self._administrative_context.resolve(address.coordinates)
        if context.neighborhood is None:
            raise NeighborhoodContextNotFoundError
        result = await self._indicators.fetch(context.neighborhood.code)
        if result.neighborhood.code != context.neighborhood.code:
            raise NeighborhoodContextNotFoundError
        return replace(result, neighborhood=context.neighborhood)
