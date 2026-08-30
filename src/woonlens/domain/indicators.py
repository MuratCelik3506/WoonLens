from dataclasses import dataclass

from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.administrative import AdministrativeArea


@dataclass(frozen=True, slots=True)
class NeighborhoodIndicator:
    """One explicitly neighbourhood-level CBS statistic."""

    key: str
    measure_id: str
    label: str
    value: float | None
    unit: str
    source_unit: str
    missing_reason: str | None = None

    def __post_init__(self) -> None:
        if not all(
            (self.key, self.measure_id, self.label, self.unit, self.source_unit)
        ):
            raise ValueError("indicator identity, labels, and units are required")
        if (self.value is None) == (self.missing_reason is None):
            raise ValueError(
                "indicator must contain either a value or a missing reason"
            )


@dataclass(frozen=True, slots=True)
class NeighborhoodIndicators:
    """Selected live indicators for one official CBS neighbourhood."""

    neighborhood: AdministrativeArea
    dataset_id: str
    dataset_year: int
    indicators: tuple[NeighborhoodIndicator, ...]
    source: SourceMetadata

    def __post_init__(self) -> None:
        if not self.dataset_id or self.dataset_year < 2000:
            raise ValueError("a valid dataset identity and year are required")
        if not self.indicators:
            raise ValueError("at least one indicator is required")
        keys = [indicator.key for indicator in self.indicators]
        if len(keys) != len(set(keys)):
            raise ValueError("indicator keys must be unique")
