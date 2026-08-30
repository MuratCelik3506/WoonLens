from datetime import datetime

import pytest

from woonlens.domain.addresses import Coordinates, SourceMetadata


@pytest.mark.parametrize(
    ("longitude", "latitude"),
    [(181.0, 52.0), (-181.0, 52.0), (4.0, 91.0), (4.0, -91.0)],
)
def test_coordinates_reject_values_outside_crs84_bounds(
    longitude: float, latitude: float
) -> None:
    with pytest.raises(ValueError):
        Coordinates(longitude, latitude)


def test_source_metadata_requires_timezone_aware_retrieval_time() -> None:
    with pytest.raises(ValueError):
        SourceMetadata(
            provider="PDOK",
            dataset="Synthetic",
            retrieved_at=datetime(2026, 8, 30),
            license_name="CC BY 4.0",
        )
