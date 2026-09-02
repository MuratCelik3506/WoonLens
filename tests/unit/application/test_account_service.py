from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.errors import AccountNotFoundError
from woonlens.application.services.accounts import AccountService
from woonlens.domain.accounts import (
    Account,
    ExternalIdentity,
    FavouriteAddressReference,
    SavedComparison,
)


class InMemoryAccountRepository:
    def __init__(self) -> None:
        self.account: Account | None = None

    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        if self.account is not None and self.account.identity == identity:
            return self.account
        return None

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        if self.account is None:
            self.account = Account(
                id=UUID("806f3a79-8ca8-4df4-903f-cbd592fc0a81"),
                identity=identity,
                created_at=datetime(2026, 9, 2, tzinfo=UTC),
            )
        return self.account

    async def delete_by_identity(self, identity: ExternalIdentity) -> bool:
        if self.account is None or self.account.identity != identity:
            return False
        self.account = None
        return True


class InMemoryFavourites:
    def __init__(self, item: FavouriteAddressReference) -> None:
        self.item = item

    async def list_for_owner(
        self, account_id: UUID
    ) -> tuple[FavouriteAddressReference, ...]:
        return (self.item,)


class InMemoryComparisons:
    def __init__(self, item: SavedComparison) -> None:
        self.item = item

    async def list_for_owner(self, account_id: UUID) -> tuple[SavedComparison, ...]:
        return (self.item,)


@pytest.mark.anyio
async def test_account_service_idempotently_ensures_and_reads_account() -> None:
    repository = InMemoryAccountRepository()
    service = AccountService(repository)
    identity = ExternalIdentity("https://identity.example", "subject")

    first = await service.ensure_account(identity)
    second = await service.ensure_account(identity)

    assert first == second
    assert await service.current_account(identity) == first
    assert (
        await service.current_account(
            ExternalIdentity("https://identity.example", "another")
        )
        is None
    )


@pytest.mark.anyio
async def test_account_service_exports_owned_recipes_and_deletes_account() -> None:
    repository = InMemoryAccountRepository()
    identity = ExternalIdentity("https://identity.example", "subject")
    favourite = FavouriteAddressReference(
        UUID("6820515e-f196-4481-aa23-ace8faf1d070"),
        UUID("e30d6355-d2f1-442f-a073-abe003bec76c"),
        datetime(2026, 9, 2, tzinfo=UTC),
    )
    comparison = SavedComparison(
        UUID("aefb6760-e730-44e8-b655-adfd44f21ca0"),
        "Shortlist",
        (
            UUID("e30d6355-d2f1-442f-a073-abe003bec76c"),
            UUID("3f439b54-0a81-4d90-acf0-2cdb75fc8626"),
        ),
        datetime(2026, 9, 2, tzinfo=UTC),
        datetime(2026, 9, 2, tzinfo=UTC),
    )
    service = AccountService(
        repository, InMemoryFavourites(favourite), InMemoryComparisons(comparison)
    )  # type: ignore[arg-type]
    account = await service.ensure_account(identity)

    snapshot = await service.export_data(identity)
    assert snapshot.account == account
    assert snapshot.favourites == (favourite,)
    assert snapshot.saved_comparisons == (comparison,)

    await service.delete_account(identity)
    assert await service.current_account(identity) is None
    with pytest.raises(AccountNotFoundError):
        await service.delete_account(identity)
