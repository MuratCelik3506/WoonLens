from typing import Protocol

from woonlens.domain.accounts import Account, ExternalIdentity


class AccountRepository(Protocol):
    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        """Return the account mapped to one exact issuer/subject pair."""

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        """Return one idempotently created account for the identity."""
