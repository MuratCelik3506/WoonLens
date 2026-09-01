from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from woonlens.application.services.comparison import LiveHomeComparisonService
from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.overview import HomeOverview
from woonlens.domain.reporting import ComparisonEvidenceReport

REPORT_SCHEMA_VERSION = "1.0.0"
REPORT_LIMITATIONS = (
    "This report is informational and is not a valuation, inspection, legal, "
    "financial, or structural conclusion.",
    "Provider datasets can use different definitions, scopes, and reference dates; "
    "consult each included source record before comparing values.",
    "Missing or unavailable source data remains missing and must not be interpreted "
    "as zero or as evidence that a condition does not exist.",
    "The report reflects live data retrieved for this request and is not retained by "
    "WoonLens.",
)


class ComparisonEvidenceReportService:
    def __init__(
        self,
        comparison_service: LiveHomeComparisonService,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._comparison_service = comparison_service
        self._clock = clock or (lambda: datetime.now(UTC))

    async def generate(self, address_ids: tuple[UUID, ...]) -> ComparisonEvidenceReport:
        comparison = await self._comparison_service.compare(address_ids)
        generated_at = self._clock()
        if generated_at.tzinfo is None:
            raise ValueError("report clock must return a timezone-aware datetime")
        sources: list[SourceMetadata] = []
        for home in comparison.homes:
            if home.overview is not None:
                sources.extend(_overview_sources(home.overview))
        return ComparisonEvidenceReport(
            schema_version=REPORT_SCHEMA_VERSION,
            generated_at=generated_at,
            comparison=comparison,
            sources=_unique_sources(sources),
            limitations=REPORT_LIMITATIONS,
        )


def _overview_sources(overview: HomeOverview) -> tuple[SourceMetadata, ...]:
    sources = [overview.address.source]
    if overview.property is not None:
        sources.append(overview.property.source)
    if overview.energy_registration is not None:
        sources.append(overview.energy_registration.source)
    if overview.administrative_context is not None:
        sources.extend(overview.administrative_context.sources)
    if overview.neighborhood_indicators is not None:
        sources.append(overview.neighborhood_indicators.source)
    return tuple(sources)


def _unique_sources(sources: list[SourceMetadata]) -> tuple[SourceMetadata, ...]:
    unique: list[SourceMetadata] = []
    seen: set[tuple[str, str, datetime, str]] = set()
    for source in sources:
        identity = (
            source.provider,
            source.dataset,
            source.retrieved_at,
            source.license_name,
        )
        if identity not in seen:
            seen.add(identity)
            unique.append(source)
    return tuple(unique)
