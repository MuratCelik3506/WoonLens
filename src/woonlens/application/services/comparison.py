import asyncio
from collections.abc import Callable
from uuid import UUID

from woonlens.application.errors import WoonLensError
from woonlens.application.ports.overview import HomeOverviewPort
from woonlens.application.services.interpretation import (
    RULES_VERSION,
    audit_homes,
    interpret_metrics,
)
from woonlens.domain.comparison import (
    ComparedHome,
    ComparedValue,
    ComparisonNotice,
    LiveHomeComparison,
    MetricComparison,
    MetricDefinition,
    MetricScalar,
)
from woonlens.domain.overview import HomeOverview

Extractor = Callable[[HomeOverview], tuple[MetricScalar | None, str | None]]


def _section_reason(overview: HomeOverview, section: str) -> str:
    return next(
        (
            item.reason
            for item in overview.unavailable_sections
            if item.section == section
        ),
        "not_reported",
    )


def _property_area(overview: HomeOverview) -> tuple[MetricScalar | None, str | None]:
    if overview.property is None:
        return None, _section_reason(overview, "property")
    value = overview.property.residential_unit.registered_area_m2
    return (value, None) if value is not None else (None, "not_reported")


def _construction_year(
    overview: HomeOverview,
) -> tuple[MetricScalar | None, str | None]:
    if overview.property is None:
        return None, _section_reason(overview, "property")
    if not overview.property.buildings:
        return None, "no_related_building"
    if len(overview.property.buildings) > 1:
        return None, "multiple_related_buildings"
    value = overview.property.buildings[0].construction_year
    return (value, None) if value is not None else (None, "not_reported")


def _energy_value(
    overview: HomeOverview,
    field: str,
) -> tuple[MetricScalar | None, str | None]:
    if overview.energy_registration is None:
        return None, _section_reason(overview, "energy_registration")
    value = getattr(overview.energy_registration.registration, field)
    return (value, None) if value is not None else (None, "not_reported")


def _average_woz(overview: HomeOverview) -> tuple[MetricScalar | None, str | None]:
    if overview.neighborhood_indicators is None:
        return None, _section_reason(overview, "neighborhood_indicators")
    indicator = next(
        (
            item
            for item in overview.neighborhood_indicators.indicators
            if item.key == "average_woz_value"
        ),
        None,
    )
    if indicator is None:
        return None, "not_reported"
    if indicator.value is None:
        return None, indicator.missing_reason or "not_reported"
    return indicator.value, None


def _air_quality_value(
    overview: HomeOverview, pollutant: str
) -> tuple[MetricScalar | None, str | None]:
    if overview.air_quality is None:
        return None, _section_reason(overview, "air_quality")
    observation = next(
        (
            item
            for item in overview.air_quality.observations
            if item.pollutant == pollutant
        ),
        None,
    )
    if observation is None:
        return None, "no_recent_compatible_station_reading"
    return observation.value, None


METRICS: tuple[tuple[MetricDefinition, Extractor], ...] = (
    (
        MetricDefinition(
            "registered_area_m2",
            "Registered BAG area",
            "property",
            "m²",
            "Official BAG registered area; not measured living area.",
            True,
        ),
        _property_area,
    ),
    (
        MetricDefinition(
            "construction_year",
            "Construction year",
            "building",
            "year",
            "BAG construction year when exactly one building is related.",
            True,
        ),
        _construction_year,
    ),
    (
        MetricDefinition(
            "energy_class",
            "Energy class",
            "property",
            "class",
            "Current EP-Online categorical energy class.",
            False,
        ),
        lambda overview: _energy_value(overview, "energy_class"),
    ),
    (
        MetricDefinition(
            "thermal_zone_area_m2",
            "Thermal-zone area",
            "property",
            "m²",
            "EP-Online calculation area; not the same definition as BAG area.",
            True,
        ),
        lambda overview: _energy_value(overview, "thermal_zone_area_m2"),
    ),
    (
        MetricDefinition(
            "energy_demand_kwh_m2_year",
            "Energy demand",
            "property",
            "kWh/m²/year",
            "EP-Online energy demand per square metre per year.",
            True,
        ),
        lambda overview: _energy_value(overview, "energy_demand_kwh_m2_year"),
    ),
    (
        MetricDefinition(
            "primary_fossil_energy_kwh_m2_year",
            "Primary fossil energy",
            "property",
            "kWh/m²/year",
            "EP-Online primary fossil energy per square metre per year.",
            True,
        ),
        lambda overview: _energy_value(overview, "primary_fossil_energy_kwh_m2_year"),
    ),
    (
        MetricDefinition(
            "renewable_energy_share_pct",
            "Renewable-energy share",
            "property",
            "%",
            "EP-Online share of renewable energy.",
            True,
        ),
        lambda overview: _energy_value(overview, "renewable_energy_share_pct"),
    ),
    (
        MetricDefinition(
            "average_woz_value",
            "Neighbourhood average WOZ value",
            "neighborhood",
            "EUR",
            "CBS neighbourhood average, not the selected property's valuation.",
            True,
        ),
        _average_woz,
    ),
    *(
        (
            MetricDefinition(
                f"air_quality_{pollutant.lower().replace('.', '_')}",
                f"Latest nearby-station {pollutant}",
                "monitoring-station",
                "µg/m³",
                "Recent unratified observation at the nearest active compatible "
                "station; not measured at the selected address.",
                False,
            ),
            lambda overview, pollutant=pollutant: _air_quality_value(
                overview, pollutant
            ),
        )
        for pollutant in ("NO2", "PM10", "PM2.5")
    ),
)


class LiveHomeComparisonService:
    def __init__(self, overviews: HomeOverviewPort) -> None:
        self._overviews = overviews

    async def compare(self, address_ids: tuple[UUID, ...]) -> LiveHomeComparison:
        if not 2 <= len(address_ids) <= 5 or len(address_ids) != len(set(address_ids)):
            raise ValueError("comparison requires two to five unique addresses")
        homes = tuple(
            await asyncio.gather(
                *(self._resolve_home(address_id) for address_id in address_ids)
            )
        )
        metrics = tuple(
            self._compare_metric(definition, extractor, homes)
            for definition, extractor in METRICS
        )
        return LiveHomeComparison(
            homes,
            metrics,
            (
                ComparisonNotice(
                    "area_definition_difference",
                    "BAG registered area and EP-Online thermal-zone area use "
                    "different definitions and are not subtracted from each other.",
                ),
                ComparisonNotice(
                    "neighborhood_context",
                    "Neighbourhood values describe local context, not the "
                    "selected home.",
                ),
                ComparisonNotice(
                    "monitoring_station_context",
                    "Air-quality values are recent unratified observations at "
                    "nearby monitoring stations, not measurements at the selected "
                    "addresses or health conclusions.",
                ),
            ),
            RULES_VERSION,
            interpret_metrics(metrics),
            audit_homes(homes),
        )

    async def _resolve_home(self, address_id: UUID) -> ComparedHome:
        try:
            return ComparedHome(address_id, await self._overviews.resolve(address_id))
        except WoonLensError as exc:
            return ComparedHome(address_id, None, exc.code)

    @staticmethod
    def _compare_metric(
        definition: MetricDefinition,
        extractor: Extractor,
        homes: tuple[ComparedHome, ...],
    ) -> MetricComparison:
        extracted = [
            (
                extractor(home.overview)
                if home.overview is not None
                else (None, home.unavailable_reason or "home_unavailable")
            )
            for home in homes
        ]
        baseline_index = next(
            (index for index, (value, _) in enumerate(extracted) if value is not None),
            None,
        )
        baseline = extracted[baseline_index][0] if baseline_index is not None else None
        values = []
        for index, (home, (value, reason)) in enumerate(
            zip(homes, extracted, strict=True)
        ):
            delta = None
            if (
                definition.supports_delta
                and isinstance(value, (int, float))
                and isinstance(baseline, (int, float))
            ):
                delta = value - baseline
            values.append(
                ComparedValue(
                    home.address_id,
                    value,
                    delta,
                    reason,
                    index == baseline_index,
                )
            )
        return MetricComparison(definition, tuple(values))
