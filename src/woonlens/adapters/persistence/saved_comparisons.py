from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from woonlens.adapters.persistence.models import (
    SavedComparisonAddressReferenceRow,
    SavedComparisonRow,
)
from woonlens.domain.accounts import SavedComparison


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SqlAlchemySavedComparisonRepository:
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

    async def list_for_owner(self, account_id: UUID) -> tuple[SavedComparison, ...]:
        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(SavedComparisonRow)
                    .where(SavedComparisonRow.account_id == account_id)
                    .order_by(SavedComparisonRow.updated_at.desc())
                )
            ).all()
            return tuple([await self._to_domain(session, row) for row in rows])

    async def get_for_owner(
        self, account_id: UUID, comparison_id: UUID
    ) -> SavedComparison | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(SavedComparisonRow).where(
                    SavedComparisonRow.id == comparison_id,
                    SavedComparisonRow.account_id == account_id,
                )
            )
            return await self._to_domain(session, row) if row is not None else None

    async def create(
        self, account_id: UUID, name: str, address_ids: tuple[UUID, ...]
    ) -> SavedComparison:
        now = self._clock()
        row = SavedComparisonRow(
            id=self._id_factory(),
            account_id=account_id,
            name=name,
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session, session.begin():
            session.add(row)
            # The child rows carry UUID values rather than ORM relationships, so
            # make the parent visible to the foreign key before inserting them.
            await session.flush()
            session.add_all(
                SavedComparisonAddressReferenceRow(
                    saved_comparison_id=row.id,
                    position=position,
                    pdok_address_id=address_id,
                )
                for position, address_id in enumerate(address_ids)
            )
        return SavedComparison(row.id, name, address_ids, now, now)

    async def update_name(
        self, account_id: UUID, comparison_id: UUID, name: str
    ) -> SavedComparison | None:
        async with self._session_factory() as session, session.begin():
            updated_at = self._clock()
            updated_id = await session.scalar(
                update(SavedComparisonRow)
                .where(
                    SavedComparisonRow.id == comparison_id,
                    SavedComparisonRow.account_id == account_id,
                )
                .values(name=name, updated_at=updated_at)
                .returning(SavedComparisonRow.id)
            )
        return (
            await self.get_for_owner(account_id, updated_id)
            if updated_id is not None
            else None
        )

    async def delete_for_owner(self, account_id: UUID, comparison_id: UUID) -> bool:
        async with self._session_factory() as session, session.begin():
            deleted_id = await session.scalar(
                delete(SavedComparisonRow)
                .where(
                    SavedComparisonRow.id == comparison_id,
                    SavedComparisonRow.account_id == account_id,
                )
                .returning(SavedComparisonRow.id)
            )
            return deleted_id is not None

    @staticmethod
    async def _to_domain(
        session: AsyncSession, row: SavedComparisonRow
    ) -> SavedComparison:
        address_ids = tuple(
            (
                await session.scalars(
                    select(SavedComparisonAddressReferenceRow.pdok_address_id)
                    .where(
                        SavedComparisonAddressReferenceRow.saved_comparison_id == row.id
                    )
                    .order_by(SavedComparisonAddressReferenceRow.position)
                )
            ).all()
        )
        return SavedComparison(
            row.id, row.name, address_ids, row.created_at, row.updated_at
        )
