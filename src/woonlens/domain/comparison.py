from dataclasses import dataclass
from uuid import UUID

from woonlens.domain.overview import HomeOverview

MetricScalar = int | float | str


@dataclass(frozen=True, slots=True)
class ComparedHome:
    address_id: UUID
    overview: HomeOverview | None
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        if (self.overview is None) == (self.unavailable_reason is None):
            raise ValueError("home must contain an overview or unavailable reason")
        if self.overview is not None and self.overview.address.id != self.address_id:
            raise ValueError("overview address must match the requested address")


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    key: str
    label: str
    scope: str
    unit: str
    definition: str
    supports_delta: bool

    def __post_init__(self) -> None:
        if not all((self.key, self.label, self.scope, self.unit, self.definition)):
            raise ValueError("metric definition fields are required")


@dataclass(frozen=True, slots=True)
class ComparedValue:
    address_id: UUID
    value: MetricScalar | None
    delta_from_baseline: float | int | None
    missing_reason: str | None
    is_baseline: bool

    def __post_init__(self) -> None:
        if (self.value is None) == (self.missing_reason is None):
            raise ValueError("compared value requires a value or missing reason")
        if self.value is None and (
            self.delta_from_baseline is not None or self.is_baseline
        ):
            raise ValueError("missing values cannot be baselines or have deltas")


@dataclass(frozen=True, slots=True)
class MetricComparison:
    metric: MetricDefinition
    values: tuple[ComparedValue, ...]


@dataclass(frozen=True, slots=True)
class ComparisonNotice:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ComparisonInsight:
    rule_id: str
    metric_key: str
    classification: str
    address_ids: tuple[UUID, ...]
    message: str

    def __post_init__(self) -> None:
        if not all((self.rule_id, self.metric_key, self.classification, self.message)):
            raise ValueError("comparison insight fields are required")


@dataclass(frozen=True, slots=True)
class SourceAudit:
    rule_id: str
    address_id: UUID
    classification: str
    fields: tuple[str, str]
    values: tuple[MetricScalar | None, MetricScalar | None]
    message: str

    def __post_init__(self) -> None:
        if not all((self.rule_id, self.classification, *self.fields, self.message)):
            raise ValueError("source audit fields are required")


@dataclass(frozen=True, slots=True)
class LiveHomeComparison:
    homes: tuple[ComparedHome, ...]
    metrics: tuple[MetricComparison, ...]
    notices: tuple[ComparisonNotice, ...]
    rules_version: str = "1.0.0"
    insights: tuple[ComparisonInsight, ...] = ()
    audits: tuple[SourceAudit, ...] = ()

    def __post_init__(self) -> None:
        if not 2 <= len(self.homes) <= 5:
            raise ValueError("comparison requires between two and five homes")
        ids = [home.address_id for home in self.homes]
        if len(ids) != len(set(ids)):
            raise ValueError("comparison homes must be unique")
        if any(len(metric.values) != len(self.homes) for metric in self.metrics):
            raise ValueError("every metric must contain one value per home")
        if not self.rules_version:
            raise ValueError("comparison rules version is required")
