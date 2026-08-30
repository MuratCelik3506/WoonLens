from typing import Protocol
from uuid import UUID

from woonlens.domain.addresses import AddressSuggestion, ResolvedAddress


class AddressSearchPort(Protocol):
    """Find compact official address candidates."""

    async def suggest(
        self, query: str, *, limit: int
    ) -> tuple[AddressSuggestion, ...]: ...


class AddressDetailsPort(Protocol):
    """Resolve one selected address identity."""

    async def resolve(self, address_id: UUID) -> ResolvedAddress: ...
