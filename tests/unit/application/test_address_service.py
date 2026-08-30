from uuid import UUID

import pytest

from woonlens.application.errors import InvalidAddressQueryError
from woonlens.application.services.addresses import AddressService
from woonlens.domain.addresses import AddressSuggestion, ResolvedAddress


class SearchStub:
    def __init__(self) -> None:
        self.call: tuple[str, int] | None = None

    async def suggest(self, query: str, *, limit: int) -> tuple[AddressSuggestion, ...]:
        self.call = (query, limit)
        return ()


class DetailsStub:
    async def resolve(self, address_id: UUID) -> ResolvedAddress:
        raise AssertionError(address_id)


@pytest.mark.anyio
async def test_suggest_normalizes_query_and_applies_configured_limit() -> None:
    search = SearchStub()
    service = AddressService(search, DetailsStub(), suggestion_limit=8)

    assert await service.suggest("  Damrak  ") == ()
    assert search.call == ("Damrak", 8)


@pytest.mark.anyio
@pytest.mark.parametrize("query", ["", " ", "a", "x" * 201])
async def test_suggest_rejects_invalid_query_before_calling_port(query: str) -> None:
    search = SearchStub()
    service = AddressService(search, DetailsStub(), suggestion_limit=8)

    with pytest.raises(InvalidAddressQueryError):
        await service.suggest(query)

    assert search.call is None
