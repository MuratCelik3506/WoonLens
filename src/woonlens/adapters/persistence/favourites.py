from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from woonlens.adapters.persistence.models import FavouriteAddressReferenceRow
from woonlens.domain.accounts import FavouriteAddressReference


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SqlAlchemyFavouriteRepository:
    """Owner-scoped PostgreSQL persistence for opaque PDOK references."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        clock: Callable[[], datetime] = _utc_now,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock
        self._id_factory = id_factory

    async def list_for_owner(
        self, account_id: UUID
    ) -> tuple[FavouriteAddressReference, ...]:
        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(FavouriteAddressReferenceRow)
                    .where(FavouriteAddressReferenceRow.account_id == account_id)
                    .order_by(FavouriteAddressReferenceRow.created_at.desc())
                )
            ).all()
        return tuple(self._to_domain(row) for row in rows)

    async def get_for_owner(
        self, account_id: UUID, favourite_id: UUID
    ) -> FavouriteAddressReference | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(FavouriteAddressReferenceRow).where(
                    FavouriteAddressReferenceRow.id == favourite_id,
                    FavouriteAddressReferenceRow.account_id == account_id,
                )
            )
        return self._to_domain(row) if row is not None else None

    async def add(
        self, account_id: UUID, pdok_address_id: UUID
    ) -> FavouriteAddressReference:
        async with self._session_factory() as session, session.begin():
            statement = (
                insert(FavouriteAddressReferenceRow)
                .values(
                    id=self._id_factory(),
                    account_id=account_id,
                    pdok_address_id=pdok_address_id,
                    created_at=self._clock(),
                )
                .on_conflict_do_nothing(constraint="uq_favourite_owner_address")
                .returning(FavouriteAddressReferenceRow)
            )
            row = (await session.scalars(statement)).one_or_none()
            if row is None:
                row = (
                    await session.scalars(
                        select(FavouriteAddressReferenceRow).where(
                            FavouriteAddressReferenceRow.account_id == account_id,
                            FavouriteAddressReferenceRow.pdok_address_id
                            == pdok_address_id,
                        )
                    )
                ).one()
            return self._to_domain(row)

    async def delete_for_owner(self, account_id: UUID, favourite_id: UUID) -> bool:
        async with self._session_factory() as session, session.begin():
            deleted_id = await session.scalar(
                delete(FavouriteAddressReferenceRow)
                .where(
                    FavouriteAddressReferenceRow.id == favourite_id,
                    FavouriteAddressReferenceRow.account_id == account_id,
                )
                .returning(FavouriteAddressReferenceRow.id)
            )
            return deleted_id is not None

    @staticmethod
    def _to_domain(row: FavouriteAddressReferenceRow) -> FavouriteAddressReference:
        return FavouriteAddressReference(
            id=row.id,
            pdok_address_id=row.pdok_address_id,
            created_at=row.created_at,
        )
