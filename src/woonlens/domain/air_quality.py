from dataclasses import dataclass
from datetime import datetime

from woonlens.domain.addresses import Coordinates, SourceMetadata

SUPPORTED_POLLUTANTS = {"NO2", "PM10", "PM2.5"}


@dataclass(frozen=True, slots=True)
class MonitoringStation:
    id: str
    name: str
    operator: str
    station_type: str
    coordinates: Coordinates
    distance_km: float

    def __post_init__(self) -> None:
        if not all((self.id, self.name, self.operator, self.station_type)):
            raise ValueError("station identity and context are required")
        if self.distance_km < 0:
            raise ValueError("station distance cannot be negative")


@dataclass(frozen=True, slots=True)
class AirQualityObservation:
    pollutant: str
    label: str
    value: float
    unit: str
    measured_from: datetime
    measured_until: datetime
    station: MonitoringStation
    status: str = "current-unratified"
    scope: str = "monitoring-station"

    def __post_init__(self) -> None:
        if self.pollutant not in SUPPORTED_POLLUTANTS:
            raise ValueError("unsupported air-quality pollutant")
        if not self.label or not self.unit:
            raise ValueError("observation label and unit are required")
        if self.measured_from.tzinfo is None or self.measured_until.tzinfo is None:
            raise ValueError("measurement times must be timezone-aware")
        if self.measured_until <= self.measured_from:
            raise ValueError("measurement window must have a positive duration")
        if self.scope != "monitoring-station":
            raise ValueError("air quality must remain station-level context")


@dataclass(frozen=True, slots=True)
class AirQualityContext:
    observations: tuple[AirQualityObservation, ...]
    missing_pollutants: tuple[str, ...]
    source: SourceMetadata
    limitation: str

    def __post_init__(self) -> None:
        pollutants = [item.pollutant for item in self.observations]
        if len(pollutants) != len(set(pollutants)):
            raise ValueError("air-quality pollutants must be unique")
        if set(pollutants) & set(self.missing_pollutants):
            raise ValueError("a pollutant cannot be present and missing")
        if set(pollutants) | set(self.missing_pollutants) != SUPPORTED_POLLUTANTS:
            raise ValueError("every supported pollutant requires a result")
        if not self.limitation:
            raise ValueError("station representativeness limitation is required")
