from collections.abc import Callable

from woonlens.domain.comparison import (
    ComparedHome,
    ComparedValue,
    ComparisonInsight,
    MetricComparison,
    MetricScalar,
    SourceAudit,
)

RULES_VERSION = "1.1.0"


def _usable(metric: MetricComparison) -> list[ComparedValue]:
    return [value for value in metric.values if value.value is not None]


def _same(values: list[ComparedValue]) -> bool:
    return len({value.value for value in values}) == 1


def _numeric_extreme(
    metric: MetricComparison,
    *,
    select: Callable[[list[float | int]], float | int],
    classification: str,
    message: str,
) -> ComparisonInsight:
    usable = [
        value for value in _usable(metric) if isinstance(value.value, (int, float))
    ]
    if len(usable) < 2:
        return ComparisonInsight(
            f"{metric.metric.key}.availability",
            metric.metric.key,
            "insufficient_data",
            tuple(value.address_id for value in usable),
            "Fewer than two homes have a usable value for this metric.",
        )
    if _same(usable):
        return ComparisonInsight(
            f"{metric.metric.key}.same",
            metric.metric.key,
            "same",
            tuple(value.address_id for value in usable),
            "All homes with available data report the same value for this metric.",
        )
    numeric_values: list[float | int] = []
    for value in usable:
        if isinstance(value.value, (int, float)):
            numeric_values.append(value.value)
    extreme = select(numeric_values)
    selected_ids = tuple(value.address_id for value in usable if value.value == extreme)
    return ComparisonInsight(
        f"{metric.metric.key}.extreme",
        metric.metric.key,
        classification,
        selected_ids,
        message,
    )


def _energy_class(metric: MetricComparison) -> ComparisonInsight:
    usable = _usable(metric)
    if len(usable) < 2:
        return ComparisonInsight(
            "energy_class.availability",
            metric.metric.key,
            "insufficient_data",
            tuple(value.address_id for value in usable),
            "Fewer than two homes have a current reported energy class.",
        )
    if _same(usable):
        return ComparisonInsight(
            "energy_class.same",
            metric.metric.key,
            "same",
            tuple(value.address_id for value in usable),
            "All homes with available data report the same energy class.",
        )
    return ComparisonInsight(
        "energy_class.categorical",
        metric.metric.key,
        "not_ranked",
        tuple(value.address_id for value in usable),
        "Energy classes are shown as official categories without an invented "
        "numeric score or overall winner.",
    )


def _station_context(metric: MetricComparison) -> ComparisonInsight:
    usable = _usable(metric)
    if not usable:
        return ComparisonInsight(
            f"{metric.metric.key}.availability",
            metric.metric.key,
            "insufficient_data",
            (),
            "No home has a recent compatible monitoring-station reading for "
            "this pollutant.",
        )
    return ComparisonInsight(
        f"{metric.metric.key}.station_context",
        metric.metric.key,
        "not_ranked",
        tuple(value.address_id for value in usable),
        "Nearby-station observations are shown as environmental context and are "
        "not ranked because station distance, type, weather, and measurement time "
        "can differ between homes.",
    )


INSIGHT_RULES: dict[
    str,
    tuple[Callable[[list[float | int]], float | int], str, str],
] = {
    "registered_area_m2": (
        max,
        "descriptive_extreme",
        "This home has the largest reported BAG registered area; larger is a "
        "preference fact, not an overall quality verdict.",
    ),
    "construction_year": (
        max,
        "descriptive_extreme",
        "This home has the newest unambiguous BAG construction year; newer does "
        "not by itself mean better condition.",
    ),
    "thermal_zone_area_m2": (
        max,
        "descriptive_extreme",
        "This home has the largest EP-Online thermal-zone area; it is not the "
        "same measurement as BAG registered area.",
    ),
    "energy_demand_kwh_m2_year": (
        min,
        "directional_indicator",
        "This home has the lowest reported energy demand per square metre; this "
        "is not a utility bill or performance guarantee.",
    ),
    "primary_fossil_energy_kwh_m2_year": (
        min,
        "directional_indicator",
        "This home has the lowest reported primary fossil energy per square "
        "metre; this is not a utility bill or performance guarantee.",
    ),
    "renewable_energy_share_pct": (
        max,
        "directional_indicator",
        "This home has the highest reported renewable-energy share in the "
        "current EP-Online registrations.",
    ),
    "average_woz_value": (
        max,
        "context_only",
        "This home is in the neighbourhood with the highest reported average "
        "WOZ value; this is not a valuation of the selected property.",
    ),
}


def interpret_metrics(
    metrics: tuple[MetricComparison, ...],
) -> tuple[ComparisonInsight, ...]:
    insights = []
    for metric in metrics:
        if metric.metric.key.startswith("air_quality_"):
            insights.append(_station_context(metric))
            continue
        if metric.metric.key == "energy_class":
            insights.append(_energy_class(metric))
            continue
        rule = INSIGHT_RULES.get(metric.metric.key)
        if rule is None:
            continue
        select, classification, message = rule
        insights.append(
            _numeric_extreme(
                metric,
                select=select,
                classification=classification,
                message=message,
            )
        )
    return tuple(insights)


def _property_year(home: ComparedHome) -> int | None:
    overview = home.overview
    if overview is None or overview.property is None:
        return None
    if len(overview.property.buildings) != 1:
        return None
    return overview.property.buildings[0].construction_year


def _energy_field(home: ComparedHome, field: str) -> MetricScalar | None:
    overview = home.overview
    if overview is None or overview.energy_registration is None:
        return None
    value = getattr(overview.energy_registration.registration, field)
    return value if isinstance(value, (int, float, str)) else None


def _area_audit(home: ComparedHome) -> SourceAudit:
    bag_area = None
    if home.overview is not None and home.overview.property is not None:
        bag_area = home.overview.property.residential_unit.registered_area_m2
    thermal_area = _energy_field(home, "thermal_zone_area_m2")
    if bag_area is None or thermal_area is None:
        classification = "missing"
        message = (
            "Both area definitions are required before their scopes can be compared."
        )
    else:
        classification = "definition-difference"
        message = (
            "BAG registered area and EP-Online thermal-zone area describe "
            "different scopes; their numerical difference is not a register error."
        )
    return SourceAudit(
        "area.definition.v1",
        home.address_id,
        classification,
        ("bag.registered_area_m2", "ep_online.thermal_zone_area_m2"),
        (bag_area, thermal_area),
        message,
    )


def _construction_year_audit(home: ComparedHome) -> SourceAudit:
    bag_year = _property_year(home)
    energy_year = _energy_field(home, "construction_year")
    if bag_year is None or energy_year is None:
        classification = "missing"
        message = "Both construction-year fields are required for this audit."
    elif bag_year == energy_year:
        classification = "match"
        message = "BAG and EP-Online report the same construction year."
    else:
        classification = "possible-conflict"
        message = (
            "BAG and EP-Online report different construction years; the sources "
            "and registration dates should be reviewed before drawing a conclusion."
        )
    return SourceAudit(
        "construction_year.cross_source.v1",
        home.address_id,
        classification,
        ("bag.construction_year", "ep_online.construction_year"),
        (bag_year, energy_year),
        message,
    )


def audit_homes(homes: tuple[ComparedHome, ...]) -> tuple[SourceAudit, ...]:
    return tuple(
        audit
        for home in homes
        for audit in (_area_audit(home), _construction_year_audit(home))
    )
