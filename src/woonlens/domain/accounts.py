from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ExternalIdentity:
    """Stable provider-neutral identity composed from OIDC issuer and subject."""

    issuer: str
    subject: str

    def __post_init__(self) -> None:
        if not self.issuer.startswith("https://") and not self.issuer.startswith(
            "http://localhost"
        ):
            raise ValueError("issuer must use HTTPS outside local development")
        if not self.subject or len(self.subject) > 255:
            raise ValueError("subject must contain between 1 and 255 characters")


@dataclass(frozen=True, slots=True)
class Account:
    """Minimum application-owned account identity."""

    id: UUID
    identity: ExternalIdentity
    created_at: datetime

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class FavouriteAddressReference:
    """Minimum user-owned recipe for resolving one address again."""

    id: UUID
    pdok_address_id: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class SavedComparison:
    """Named, ordered recipe for rerunning a live comparison."""

    id: UUID
    name: str
    address_ids: tuple[UUID, ...]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not 1 <= len(self.name) <= 80 or self.name != self.name.strip():
            raise ValueError("name must be trimmed and contain 1 to 80 characters")
        if not 2 <= len(self.address_ids) <= 5:
            raise ValueError("a saved comparison requires two to five addresses")
        if len(set(self.address_ids)) != len(self.address_ids):
            raise ValueError("saved comparison addresses must be unique")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("saved comparison timestamps must be timezone-aware")
