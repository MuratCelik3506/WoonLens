from dataclasses import dataclass
from datetime import datetime

from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.comparison import LiveHomeComparison


@dataclass(frozen=True, slots=True)
class ComparisonEvidenceReport:
    """One request-scoped, source-attributed comparison export."""

    schema_version: str
    generated_at: datetime
    comparison: LiveHomeComparison
    sources: tuple[SourceMetadata, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("report schema version is required")
        if self.generated_at.tzinfo is None:
            raise ValueError("report generation time must be timezone-aware")
        if not self.limitations:
            raise ValueError("report limitations are required")
