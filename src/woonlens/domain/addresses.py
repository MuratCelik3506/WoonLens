from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

CRS84 = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"


@dataclass(frozen=True, slots=True)
class Coordinates:
    """A point expressed as longitude and latitude in CRS84."""

    longitude: float
    latitude: float
    crs: str = CRS84

    def __post_init__(self) -> None:
        if not -180 <= self.longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        if not -90 <= self.latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Request-scoped provenance for a provider-derived value."""

    provider: str
    dataset: str
    retrieved_at: datetime
    license_name: str

    def __post_init__(self) -> None:
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class AddressSuggestion:
    """A compact, provider-independent address search result."""

    id: UUID
    display_name: str
    coordinates: Coordinates
    source: SourceMetadata


@dataclass(frozen=True, slots=True)
class ResolvedAddress:
    """Official BAG address identity needed by later live-data joins."""

    id: UUID
    number_designation_id: str
    addressable_object_id: str
    addressable_object_type: str
    street: str
    house_number: str
    house_letter: str | None
    house_number_suffix: str | None
    postal_code: str
    city: str
    coordinates: Coordinates
    source: SourceMetadata
