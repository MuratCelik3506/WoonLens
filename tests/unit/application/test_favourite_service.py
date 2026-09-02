from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import FavouriteNotFoundError
from woonlens.application.services.favourites import FavouriteService
from woonlens.domain.accounts import (
    Account,
    ExternalIdentity,
    FavouriteAddressReference,
)

IDENTITY = ExternalIdentity("https://identity.example", "owner")
OWNER_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
FAVOURITE_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
ADDRESS_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
NOW = datetime(2026, 9, 2, tzinfo=UTC)


class Accounts:
    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        return Account(OWNER_ID, identity, NOW)

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        return Account(OWNER_ID, identity, NOW)


class Favourites:
    def __init__(self) -> None:
        self.items: dict[UUID, FavouriteAddressReference] = {}

    async def list_for_owner(
        self, account_id: UUID
    ) -> tuple[FavouriteAddressReference, ...]:
        assert account_id == OWNER_ID
        return tuple(self.items.values())

    async def get_for_owner(
        self, account_id: UUID, favourite_id: UUID
    ) -> FavouriteAddressReference | None:
        assert account_id == OWNER_ID
        return self.items.get(favourite_id)

    async def add(
        self, account_id: UUID, pdok_address_id: UUID
    ) -> FavouriteAddressReference:
        assert account_id == OWNER_ID
        existing = next(
            (
                item
                for item in self.items.values()
                if item.pdok_address_id == pdok_address_id
            ),
            None,
        )
        item = existing or FavouriteAddressReference(FAVOURITE_ID, pdok_address_id, NOW)
        self.items[item.id] = item
        return item

    async def delete_for_owner(self, account_id: UUID, favourite_id: UUID) -> bool:
        assert account_id == OWNER_ID
        return self.items.pop(favourite_id, None) is not None


class Addresses:
    async def resolve(self, address_id: UUID):  # type: ignore[no-untyped-def]
        return address_id


@pytest.mark.anyio
async def test_favourites_are_idempotent_and_owner_scoped() -> None:
    repository = Favourites()
    service = FavouriteService(Accounts(), repository, Addresses())  # type: ignore[arg-type]

    first = await service.add(IDENTITY, ADDRESS_ID)
    second = await service.add(IDENTITY, ADDRESS_ID)

    assert first == second
    assert await service.list(IDENTITY) == (first,)
    assert await service.resolve(IDENTITY, first.id) == ADDRESS_ID
    await service.delete(IDENTITY, first.id)
    with pytest.raises(FavouriteNotFoundError):
        await service.delete(IDENTITY, first.id)
