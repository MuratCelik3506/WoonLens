from dataclasses import dataclass

from woonlens.domain.addresses import SourceMetadata


def _validate_bag_id(value: str) -> None:
    if len(value) != 16 or not value.isdigit():
        raise ValueError("BAG identifiers must contain 16 digits")


@dataclass(frozen=True, slots=True)
class ResidentialUnit:
    """Selected BAG verblijfsobject facts."""

    id: str
    status: str | None
    use_purposes: tuple[str, ...]
    registered_area_m2: int | None

    def __post_init__(self) -> None:
        _validate_bag_id(self.id)
        if self.registered_area_m2 is not None and self.registered_area_m2 <= 0:
            raise ValueError("registered BAG area must be positive")


@dataclass(frozen=True, slots=True)
class Building:
    """One BAG pand related to the selected residential unit."""

    id: str
    status: str | None
    construction_year: int | None
    use_purposes: tuple[str, ...]
    residential_unit_count: int | None

    def __post_init__(self) -> None:
        _validate_bag_id(self.id)
        if (
            self.construction_year is not None
            and not 1000 <= self.construction_year <= 9999
        ):
            raise ValueError("construction year is outside the supported range")
        if self.residential_unit_count is not None and self.residential_unit_count < 0:
            raise ValueError("residential unit count cannot be negative")


@dataclass(frozen=True, slots=True)
class PropertyDetails:
    """Request-scoped BAG residential-unit and building facts."""

    residential_unit: ResidentialUnit
    buildings: tuple[Building, ...]
    source: SourceMetadata
