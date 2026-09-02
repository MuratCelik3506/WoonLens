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
