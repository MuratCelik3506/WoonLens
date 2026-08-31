from datetime import datetime

import pytest

from woonlens.domain.energy import EnergyRegistration


def registration(**overrides: object) -> EnergyRegistration:
    values: dict[str, object] = {
        "bag_object_id": "0599010000295420",
        "bag_building_ids": ("0599100000691863",),
        "registration_date": datetime(2026, 2, 4),
        "inspection_date": datetime(2026, 1, 14),
        "valid_until": datetime(2036, 1, 14),
        "assessment_type": "Basisopname",
        "registration_status": "Bestaand",
        "building_class": "Woningbouw",
        "building_type": "Appartement",
        "building_subtype": "Tussenmidden",
        "construction_year": 1873,
        "thermal_zone_area_m2": 54.41,
        "energy_class": "B",
        "energy_demand_kwh_m2_year": 109.02,
        "primary_fossil_energy_kwh_m2_year": 172.52,
        "renewable_energy_share_pct": 0.0,
        "calculated_co2_kg_m2_year": 31.8,
        "calculated_energy_use_kwh_m2_year": 172.51,
    }
    values.update(overrides)
    return EnergyRegistration(**values)  # type: ignore[arg-type]


def test_accepts_valid_energy_registration() -> None:
    assert registration().energy_class == "B"


@pytest.mark.parametrize(
    "overrides",
    [
        {"bag_object_id": "0" * 16},
        {"bag_building_ids": ("1",)},
        {"bag_building_ids": ("0599100000691863",) * 2},
        {"valid_until": datetime(2020, 1, 1)},
        {"construction_year": 999},
        {"thermal_zone_area_m2": -1.0},
    ],
)
def test_rejects_invalid_registration_values(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        registration(**overrides)
