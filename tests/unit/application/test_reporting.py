from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.application.services.comparison import LiveHomeComparisonService
from woonlens.application.services.reporting import ComparisonEvidenceReportService
from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.overview import HomeOverview, UnavailableSection

FIRST = UUID("11111111-1111-4111-8111-111111111111")
SECOND = UUID("22222222-2222-4222-8222-222222222222")
RETRIEVED_AT = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)
GENERATED_AT = datetime(2026, 8, 31, 10, 5, tzinfo=UTC)
SOURCE = SourceMetadata("PDOK", "BAG", RETRIEVED_AT, "CC0")


class OverviewFake:
    async def resolve(self, address_id: UUID) -> HomeOverview:
        return HomeOverview(
            ResolvedAddress(
                address_id,
                "0599200000508415",
                "0599010000295420",
                "Verblijfsobject",
                "Street",
                "1",
                None,
                None,
                "1234AB",
                "City",
                Coordinates(4.9, 52.37),
                SOURCE,
            ),
            None,
            None,
            None,
            None,
            (
                UnavailableSection("property", "source_unavailable"),
                UnavailableSection("energy_registration", "source_unavailable"),
                UnavailableSection("administrative_context", "source_unavailable"),
                UnavailableSection("neighborhood_indicators", "source_unavailable"),
            ),
        )


@pytest.mark.anyio
async def test_report_is_versioned_attributed_and_deterministic() -> None:
    comparison_service = LiveHomeComparisonService(OverviewFake())
    service = ComparisonEvidenceReportService(
        comparison_service, clock=lambda: GENERATED_AT
    )

    report = await service.generate((FIRST, SECOND))

    assert report.schema_version == "1.0.0"
    assert report.generated_at == GENERATED_AT
    assert report.comparison.rules_version == "1.1.0"
    assert report.sources == (SOURCE,)
    assert len(report.limitations) == 4


@pytest.mark.anyio
async def test_report_rejects_naive_clock() -> None:
    service = ComparisonEvidenceReportService(
        LiveHomeComparisonService(OverviewFake()),
        clock=lambda: datetime(2026, 8, 31),
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        await service.generate((FIRST, SECOND))
