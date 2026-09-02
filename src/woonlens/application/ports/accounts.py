from typing import Protocol
from uuid import UUID

from woonlens.domain.accounts import (
    Account,
    ExternalIdentity,
    FavouriteAddressReference,
)


class AccountRepository(Protocol):
    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        """Return the account mapped to one exact issuer/subject pair."""

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        """Return one idempotently created account for the identity."""


class FavouriteRepository(Protocol):
    async def list_for_owner(
        self, account_id: UUID
    ) -> tuple[FavouriteAddressReference, ...]: ...

    async def get_for_owner(
        self, account_id: UUID, favourite_id: UUID
    ) -> FavouriteAddressReference | None: ...

    async def add(
        self, account_id: UUID, pdok_address_id: UUID
    ) -> FavouriteAddressReference: ...

    async def delete_for_owner(self, account_id: UUID, favourite_id: UUID) -> bool: ...
