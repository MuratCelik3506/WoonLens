from typing import Protocol
from uuid import UUID

from woonlens.domain.accounts import (
    Account,
    ExternalIdentity,
    FavouriteAddressReference,
    SavedComparison,
)


class AccountRepository(Protocol):
    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        """Return the account mapped to one exact issuer/subject pair."""

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        """Return one idempotently created account for the identity."""

    async def delete_by_identity(self, identity: ExternalIdentity) -> bool:
        """Delete one account and its application-owned children atomically."""


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


class SavedComparisonRepository(Protocol):
    async def list_for_owner(self, account_id: UUID) -> tuple[SavedComparison, ...]: ...

    async def get_for_owner(
        self, account_id: UUID, comparison_id: UUID
    ) -> SavedComparison | None: ...

    async def create(
        self, account_id: UUID, name: str, address_ids: tuple[UUID, ...]
    ) -> SavedComparison: ...

    async def update_name(
        self, account_id: UUID, comparison_id: UUID, name: str
    ) -> SavedComparison | None: ...

    async def delete_for_owner(self, account_id: UUID, comparison_id: UUID) -> bool: ...
