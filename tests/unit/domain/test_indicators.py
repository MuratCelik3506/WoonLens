from datetime import UTC, datetime

import pytest

from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.administrative import AdministrativeArea
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators

SOURCE = SourceMetadata("CBS", "Dataset", datetime.now(UTC), "CC BY 4.0")


def test_indicator_requires_value_or_missing_reason_exclusively() -> None:
    with pytest.raises(ValueError):
        NeighborhoodIndicator("key", "measure", "Label", None, "%", "%")
    with pytest.raises(ValueError):
        NeighborhoodIndicator("key", "measure", "Label", 1.0, "%", "%", "suppressed")


def test_indicator_collection_rejects_duplicate_keys() -> None:
    indicator = NeighborhoodIndicator("key", "measure", "Label", 1.0, "%", "%")
    with pytest.raises(ValueError):
        NeighborhoodIndicators(
            AdministrativeArea("BU05990112", "Cool"),
            "85984NED",
            2024,
            (indicator, indicator),
            SOURCE,
        )
