from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from woonlens.adapters.persistence.models import AccountRow
from woonlens.domain.accounts import Account, ExternalIdentity


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SqlAlchemyAccountRepository:
    """PostgreSQL repository with atomic issuer/subject idempotency."""

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

    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        async with self._session_factory() as session:
            row = await session.scalar(self._identity_query(identity))
            return self._to_domain(row) if row is not None else None

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        account_id = self._id_factory()
        created_at = self._clock()
        async with self._session_factory() as session, session.begin():
            statement = (
                insert(AccountRow)
                .values(
                    id=account_id,
                    issuer=identity.issuer,
                    subject=identity.subject,
                    created_at=created_at,
                )
                .on_conflict_do_nothing(constraint="uq_account_external_identity")
                .returning(AccountRow)
            )
            row = (await session.scalars(statement)).one_or_none()
            if row is None:
                row = (await session.scalars(self._identity_query(identity))).one()
            return self._to_domain(row)

    @staticmethod
    def _identity_query(identity: ExternalIdentity):  # type: ignore[no-untyped-def]
        return select(AccountRow).where(
            AccountRow.issuer == identity.issuer,
            AccountRow.subject == identity.subject,
        )

    @staticmethod
    def _to_domain(row: AccountRow) -> Account:
        return Account(
            id=row.id,
            identity=ExternalIdentity(issuer=row.issuer, subject=row.subject),
            created_at=row.created_at,
        )
