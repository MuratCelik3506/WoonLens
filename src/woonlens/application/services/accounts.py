from woonlens.application.errors import AccountNotFoundError
from woonlens.application.ports.accounts import (
    AccountRepository,
    FavouriteRepository,
    SavedComparisonRepository,
)
from woonlens.domain.accounts import Account, AccountDataExport, ExternalIdentity


class AccountService:
    """Coordinate minimum optional-account identity persistence."""

    def __init__(
        self,
        repository: AccountRepository,
        favourites: FavouriteRepository | None = None,
        saved_comparisons: SavedComparisonRepository | None = None,
    ) -> None:
        self._repository = repository
        self._favourites = favourites
        self._saved_comparisons = saved_comparisons

    async def ensure_account(self, identity: ExternalIdentity) -> Account:
        return await self._repository.get_or_create(identity)

    async def current_account(self, identity: ExternalIdentity) -> Account | None:
        return await self._repository.find_by_identity(identity)

    async def export_data(self, identity: ExternalIdentity) -> AccountDataExport:
        account = await self._required_account(identity)
        if self._favourites is None or self._saved_comparisons is None:
            raise RuntimeError("account lifecycle repositories are unavailable")
        return AccountDataExport(
            account=account,
            favourites=await self._favourites.list_for_owner(account.id),
            saved_comparisons=await self._saved_comparisons.list_for_owner(account.id),
        )

    async def delete_account(self, identity: ExternalIdentity) -> None:
        if not await self._repository.delete_by_identity(identity):
            raise AccountNotFoundError

    async def _required_account(self, identity: ExternalIdentity) -> Account:
        account = await self.current_account(identity)
        if account is None:
            raise AccountNotFoundError
        return account
