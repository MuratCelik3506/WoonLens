from datetime import UTC, datetime

import pytest

from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.property import Building, PropertyDetails, ResidentialUnit

SOURCE = SourceMetadata("PDOK", "BAG", datetime.now(UTC), "Public Domain Mark 1.0")


def test_property_details_accept_valid_bag_facts() -> None:
    unit = ResidentialUnit("0599010000295420", "in use", ("woonfunctie",), 62)
    building = Building("0599100000691863", "in use", 1873, ("woonfunctie",), 4)

    result = PropertyDetails(unit, (building,), SOURCE)

    assert result.residential_unit.registered_area_m2 == 62
    assert result.buildings[0].construction_year == 1873


@pytest.mark.parametrize("bag_id", ["123", "abcdefghijklmnop", "0" * 17])
def test_property_facts_reject_invalid_bag_ids(bag_id: str) -> None:
    with pytest.raises(ValueError):
        ResidentialUnit(bag_id, None, (), None)


def test_property_facts_reject_impossible_values() -> None:
    with pytest.raises(ValueError):
        ResidentialUnit("0" * 16, None, (), 0)
    with pytest.raises(ValueError):
        Building("0" * 16, None, 999, (), None)
    with pytest.raises(ValueError):
        Building("0" * 16, None, None, (), -1)
