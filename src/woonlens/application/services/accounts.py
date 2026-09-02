from woonlens.application.ports.accounts import AccountRepository
from woonlens.domain.accounts import Account, ExternalIdentity


class AccountService:
    """Coordinate minimum optional-account identity persistence."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    async def ensure_account(self, identity: ExternalIdentity) -> Account:
        return await self._repository.get_or_create(identity)

    async def current_account(self, identity: ExternalIdentity) -> Account | None:
        return await self._repository.find_by_identity(identity)
