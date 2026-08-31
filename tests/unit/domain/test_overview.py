from datetime import UTC, datetime
from uuid import UUID

import pytest

from woonlens.domain.addresses import Coordinates, ResolvedAddress, SourceMetadata
from woonlens.domain.overview import HomeOverview, UnavailableSection

SOURCE = SourceMetadata("Provider", "Dataset", datetime.now(UTC), "Terms")
ADDRESS = ResolvedAddress(
    UUID("11111111-1111-4111-8111-111111111111"),
    "0599200000508415",
    "0599010000295420",
    "Verblijfsobject",
    "Street",
    "1",
    None,
    None,
    "1234AB",
    "City",
    Coordinates(4.9, 52.37),
    SOURCE,
)


def test_overview_accepts_unique_unavailable_sections() -> None:
    overview = HomeOverview(
        ADDRESS,
        None,
        None,
        None,
        None,
        (
            UnavailableSection("property", "source_unavailable"),
            UnavailableSection("energy_registration", "source_configuration_error"),
        ),
    )
    assert len(overview.unavailable_sections) == 2


def test_unavailable_section_rejects_unknown_name() -> None:
    with pytest.raises(ValueError):
        UnavailableSection("unknown", "missing")


def test_overview_rejects_duplicate_unavailable_sections() -> None:
    item = UnavailableSection("property", "missing")
    with pytest.raises(ValueError):
        HomeOverview(ADDRESS, None, None, None, None, (item, item))
