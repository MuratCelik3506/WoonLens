from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import SavedComparisonNotFoundError
from woonlens.application.services.saved_comparisons import SavedComparisonService
from woonlens.domain.accounts import Account, ExternalIdentity, SavedComparison

IDENTITY = ExternalIdentity("https://identity.example", "owner")
OWNER_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
ITEM_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
ADDRESSES = (
    UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
    UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
)
NOW = datetime(2026, 9, 2, tzinfo=UTC)


class Accounts:
    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        return Account(OWNER_ID, identity, NOW)

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        return Account(OWNER_ID, identity, NOW)

    async def delete_by_identity(self, identity: ExternalIdentity) -> bool:
        return True


class Comparisons:
    item: SavedComparison | None = None

    async def list_for_owner(self, account_id: UUID):  # type: ignore[no-untyped-def]
        return (self.item,) if self.item else ()

    async def get_for_owner(self, account_id: UUID, comparison_id: UUID):  # type: ignore[no-untyped-def]
        return self.item if self.item and self.item.id == comparison_id else None

    async def create(self, account_id: UUID, name: str, address_ids: tuple[UUID, ...]):  # type: ignore[no-untyped-def]
        self.item = SavedComparison(ITEM_ID, name, address_ids, NOW, NOW)
        return self.item

    async def update_name(self, account_id: UUID, comparison_id: UUID, name: str):  # type: ignore[no-untyped-def]
        if not self.item or self.item.id != comparison_id:
            return None
        self.item = SavedComparison(self.item.id, name, self.item.address_ids, NOW, NOW)
        return self.item

    async def delete_for_owner(self, account_id: UUID, comparison_id: UUID) -> bool:
        if not self.item or self.item.id != comparison_id:
            return False
        self.item = None
        return True


@pytest.mark.anyio
async def test_saved_comparison_lifecycle_preserves_order() -> None:
    repository = Comparisons()
    service = SavedComparisonService(Accounts(), repository)
    created = await service.create(IDENTITY, "  Shortlist  ", ADDRESSES)
    assert created.name == "Shortlist"
    assert created.address_ids == ADDRESSES
    assert await service.get(IDENTITY, ITEM_ID) == created
    assert (await service.rename(IDENTITY, ITEM_ID, "Finalists")).name == "Finalists"
    await service.delete(IDENTITY, ITEM_ID)
    with pytest.raises(SavedComparisonNotFoundError):
        await service.get(IDENTITY, ITEM_ID)
