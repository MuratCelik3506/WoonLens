from uuid import UUID

from woonlens.application.errors import AccountNotFoundError, FavouriteNotFoundError
from woonlens.application.ports.accounts import AccountRepository, FavouriteRepository
from woonlens.application.services.addresses import AddressService
from woonlens.domain.accounts import ExternalIdentity, FavouriteAddressReference
from woonlens.domain.addresses import ResolvedAddress


class FavouriteService:
    """Manage minimum address references without retaining provider facts."""

    def __init__(
        self,
        accounts: AccountRepository,
        favourites: FavouriteRepository,
        addresses: AddressService,
    ) -> None:
        self._accounts = accounts
        self._favourites = favourites
        self._addresses = addresses

    async def list(
        self, identity: ExternalIdentity
    ) -> tuple[FavouriteAddressReference, ...]:
        return await self._favourites.list_for_owner(await self._account_id(identity))

    async def add(
        self, identity: ExternalIdentity, pdok_address_id: UUID
    ) -> FavouriteAddressReference:
        return await self._favourites.add(
            await self._account_id(identity), pdok_address_id
        )

    async def delete(self, identity: ExternalIdentity, favourite_id: UUID) -> None:
        if not await self._favourites.delete_for_owner(
            await self._account_id(identity), favourite_id
        ):
            raise FavouriteNotFoundError

    async def resolve(
        self, identity: ExternalIdentity, favourite_id: UUID
    ) -> ResolvedAddress:
        favourite = await self._favourites.get_for_owner(
            await self._account_id(identity), favourite_id
        )
        if favourite is None:
            raise FavouriteNotFoundError
        return await self._addresses.resolve(favourite.pdok_address_id)

    async def _account_id(self, identity: ExternalIdentity) -> UUID:
        account = await self._accounts.find_by_identity(identity)
        if account is None:
            raise AccountNotFoundError
        return account.id
