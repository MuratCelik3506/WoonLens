from uuid import UUID

import pytest

from woonlens.domain.comparison import (
    ComparedHome,
    ComparedValue,
    LiveHomeComparison,
    MetricComparison,
    MetricDefinition,
)

FIRST = UUID("11111111-1111-4111-8111-111111111111")
SECOND = UUID("22222222-2222-4222-8222-222222222222")
METRIC = MetricDefinition("area", "Area", "property", "m²", "Definition", True)


def test_compared_value_requires_value_or_missing_reason() -> None:
    with pytest.raises(ValueError):
        ComparedValue(FIRST, None, None, None, False)
    with pytest.raises(ValueError):
        ComparedValue(FIRST, 10, None, "missing", False)


def test_comparison_requires_two_to_five_unique_homes() -> None:
    home = ComparedHome(FIRST, None, "address_not_found")
    value = ComparedValue(FIRST, None, None, "address_not_found", False)
    with pytest.raises(ValueError):
        LiveHomeComparison((home,), (MetricComparison(METRIC, (value,)),), ())

    second_value = ComparedValue(SECOND, None, None, "address_not_found", False)
    with pytest.raises(ValueError):
        LiveHomeComparison(
            (home, home),
            (MetricComparison(METRIC, (value, second_value)),),
            (),
        )
