from uuid import UUID

from woonlens.application.errors import InvalidAddressQueryError
from woonlens.application.ports.addresses import AddressDetailsPort, AddressSearchPort
from woonlens.domain.addresses import AddressSuggestion, ResolvedAddress


class AddressService:
    """Coordinate transient official-address search and resolution."""

    def __init__(
        self,
        search: AddressSearchPort,
        details: AddressDetailsPort,
        *,
        suggestion_limit: int,
    ) -> None:
        self._search = search
        self._details = details
        self._suggestion_limit = suggestion_limit

    async def suggest(self, query: str) -> tuple[AddressSuggestion, ...]:
        normalized_query = query.strip()
        if not 2 <= len(normalized_query) <= 200:
            raise InvalidAddressQueryError
        return await self._search.suggest(
            normalized_query,
            limit=self._suggestion_limit,
        )

    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        return await self._details.resolve(address_id)
