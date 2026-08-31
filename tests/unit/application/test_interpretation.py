from uuid import UUID

from woonlens.application.services.interpretation import interpret_metrics
from woonlens.domain.comparison import ComparedValue, MetricComparison, MetricDefinition

FIRST = UUID("11111111-1111-4111-8111-111111111111")
SECOND = UUID("22222222-2222-4222-8222-222222222222")


def comparison(
    key: str,
    first: int | float | str | None,
    second: int | float | str | None,
) -> MetricComparison:
    definition = MetricDefinition(key, key, "property", "unit", "definition", True)
    values = tuple(
        ComparedValue(
            address_id,
            value,
            None,
            None if value is not None else "missing",
            False,
        )
        for address_id, value in ((FIRST, first), (SECOND, second))
    )
    return MetricComparison(definition, values)


def test_equal_numeric_values_produce_same_interpretation() -> None:
    insight = interpret_metrics((comparison("registered_area_m2", 60, 60),))[0]
    assert insight.classification == "same"
    assert insight.address_ids == (FIRST, SECOND)


def test_single_value_produces_insufficient_data() -> None:
    insight = interpret_metrics((comparison("registered_area_m2", 60, None),))[0]
    assert insight.classification == "insufficient_data"
    assert insight.address_ids == (FIRST,)


def test_energy_class_is_not_ranked() -> None:
    insight = interpret_metrics((comparison("energy_class", "A", "B"),))[0]
    assert insight.classification == "not_ranked"
    assert "numeric score" in insight.message
