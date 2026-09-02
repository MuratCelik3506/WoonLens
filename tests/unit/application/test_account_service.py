from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.services.accounts import AccountService
from woonlens.domain.accounts import Account, ExternalIdentity


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
