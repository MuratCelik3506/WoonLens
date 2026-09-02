from uuid import UUID

from woonlens.application.errors import (
    AccountNotFoundError,
    SavedComparisonNotFoundError,
)
from woonlens.application.ports.accounts import (
    AccountRepository,
    SavedComparisonRepository,
)
from woonlens.domain.accounts import ExternalIdentity, SavedComparison


class SavedComparisonService:
    def __init__(
        self, accounts: AccountRepository, comparisons: SavedComparisonRepository
    ) -> None:
        self._accounts = accounts
        self._comparisons = comparisons

    async def list(self, identity: ExternalIdentity) -> tuple[SavedComparison, ...]:
        return await self._comparisons.list_for_owner(await self._owner(identity))

    async def get(
        self, identity: ExternalIdentity, comparison_id: UUID
    ) -> SavedComparison:
        result = await self._comparisons.get_for_owner(
            await self._owner(identity), comparison_id
        )
        if result is None:
            raise SavedComparisonNotFoundError
        return result

    async def create(
        self, identity: ExternalIdentity, name: str, address_ids: tuple[UUID, ...]
    ) -> SavedComparison:
        return await self._comparisons.create(
            await self._owner(identity), self._name(name), address_ids
        )

    async def rename(
        self, identity: ExternalIdentity, comparison_id: UUID, name: str
    ) -> SavedComparison:
        result = await self._comparisons.update_name(
            await self._owner(identity), comparison_id, self._name(name)
        )
        if result is None:
            raise SavedComparisonNotFoundError
        return result

    async def delete(self, identity: ExternalIdentity, comparison_id: UUID) -> None:
        if not await self._comparisons.delete_for_owner(
            await self._owner(identity), comparison_id
        ):
            raise SavedComparisonNotFoundError

    async def _owner(self, identity: ExternalIdentity) -> UUID:
        account = await self._accounts.find_by_identity(identity)
        if account is None:
            raise AccountNotFoundError
        return account.id

    @staticmethod
    def _name(value: str) -> str:
        name = value.strip()
        if not 1 <= len(name) <= 80:
            raise ValueError("name must contain 1 to 80 characters")
        return name
