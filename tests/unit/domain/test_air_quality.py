from datetime import UTC, datetime

import pytest

from woonlens.domain.addresses import Coordinates, SourceMetadata
from woonlens.domain.air_quality import (
    AirQualityContext,
    AirQualityObservation,
    MonitoringStation,
)

SOURCE = SourceMetadata("RIVM", "Luchtmeetnet", datetime.now(UTC), "Terms")
STATION = MonitoringStation(
    "NL00001", "Station", "LML", "background", Coordinates(4.0, 52.0), 1.2
)


def _observation(pollutant: str) -> AirQualityObservation:
    return AirQualityObservation(
        pollutant,
        pollutant,
        10.0,
        "µg/m³",
        datetime(2026, 9, 1, 7, tzinfo=UTC),
        datetime(2026, 9, 1, 8, tzinfo=UTC),
        STATION,
    )


def test_context_requires_one_result_per_supported_pollutant() -> None:
    context = AirQualityContext(
        (_observation("NO2"),), ("PM10", "PM2.5"), SOURCE, "Station context"
    )
    assert context.observations[0].scope == "monitoring-station"
    with pytest.raises(ValueError, match="every supported"):
        AirQualityContext((_observation("NO2"),), ("PM10",), SOURCE, "Limited")


def test_rejects_invalid_station_and_observation_contracts() -> None:
    with pytest.raises(ValueError, match="distance"):
        MonitoringStation("id", "name", "operator", "type", Coordinates(4.0, 52.0), -1)
    with pytest.raises(ValueError, match="unsupported"):
        _observation("O3")
    with pytest.raises(ValueError, match="positive duration"):
        AirQualityObservation(
            "NO2",
            "NO2",
            1.0,
            "µg/m³",
            datetime(2026, 9, 1, 8, tzinfo=UTC),
            datetime(2026, 9, 1, 8, tzinfo=UTC),
            STATION,
        )
