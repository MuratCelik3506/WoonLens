from dataclasses import dataclass
from datetime import datetime

from woonlens.domain.addresses import SourceMetadata


def _validate_bag_id(value: str) -> None:
    if len(value) != 16 or not value.isdigit() or value == "0" * 16:
        raise ValueError(
            "BAG identifier must contain 16 digits and not be a placeholder"
        )


def _non_negative(value: float | None, name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True, slots=True)
class EnergyRegistration:
    """One current official EP-Online energy-performance registration."""

    bag_object_id: str
    bag_building_ids: tuple[str, ...]
    registration_date: datetime
    inspection_date: datetime | None
    valid_until: datetime
    assessment_type: str | None
    registration_status: str | None
    building_class: str | None
    building_type: str | None
    building_subtype: str | None
    construction_year: int | None
    thermal_zone_area_m2: float | None
    energy_class: str | None
    energy_demand_kwh_m2_year: float | None
    primary_fossil_energy_kwh_m2_year: float | None
    renewable_energy_share_pct: float | None
    calculated_co2_kg_m2_year: float | None
    calculated_energy_use_kwh_m2_year: float | None

    def __post_init__(self) -> None:
        _validate_bag_id(self.bag_object_id)
        for building_id in self.bag_building_ids:
            _validate_bag_id(building_id)
        if len(self.bag_building_ids) != len(set(self.bag_building_ids)):
            raise ValueError("BAG building identifiers must be unique")
        if self.valid_until.date() < self.registration_date.date():
            raise ValueError("validity cannot end before registration")
        if (
            self.construction_year is not None
            and not 1000 <= self.construction_year <= 9999
        ):
            raise ValueError("construction year is outside the supported range")
        _non_negative(self.thermal_zone_area_m2, "thermal-zone area")
        _non_negative(self.energy_demand_kwh_m2_year, "energy demand")
        _non_negative(self.primary_fossil_energy_kwh_m2_year, "fossil energy")
        _non_negative(self.renewable_energy_share_pct, "renewable share")
        _non_negative(self.calculated_co2_kg_m2_year, "calculated CO2")
        _non_negative(self.calculated_energy_use_kwh_m2_year, "calculated energy use")


@dataclass(frozen=True, slots=True)
class EnergyRegistrationDetails:
    registration: EnergyRegistration
    source: SourceMetadata
