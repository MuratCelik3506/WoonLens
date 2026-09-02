from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    pass


class AccountRow(Base):
    __tablename__ = "account"
    __table_args__ = (
        UniqueConstraint("issuer", "subject", name="uq_account_external_identity"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    issuer: Mapped[str] = mapped_column(String(2048), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
