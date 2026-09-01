from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.comparison import ComparedHome, LiveHomeComparison
from woonlens.domain.reporting import ComparisonEvidenceReport


def _comparison() -> LiveHomeComparison:
    return LiveHomeComparison(
        homes=(
            ComparedHome(
                UUID("11111111-1111-4111-8111-111111111111"),
                None,
                "source_unavailable",
            ),
            ComparedHome(
                UUID("22222222-2222-4222-8222-222222222222"),
                None,
                "source_unavailable",
            ),
        ),
        metrics=(),
        notices=(),
    )


def test_report_requires_aware_generation_time() -> None:
    source = SourceMetadata(
        "Provider", "Dataset", datetime(2026, 1, 1, tzinfo=UTC), "Terms"
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        ComparisonEvidenceReport(
            "1.0.0",
            datetime(2026, 1, 1),
            _comparison(),
            (source,),
            ("Limited",),
        )


def test_report_requires_version_and_limitations() -> None:
    generated_at = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="schema version"):
        ComparisonEvidenceReport("", generated_at, _comparison(), (), ("Limited",))
    with pytest.raises(ValueError, match="limitations"):
        ComparisonEvidenceReport("1.0.0", generated_at, _comparison(), (), ())
