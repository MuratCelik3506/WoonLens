from datetime import UTC, datetime

import pytest

from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.administrative import AdministrativeArea, AdministrativeContext


def test_administrative_area_requires_code_and_name() -> None:
    with pytest.raises(ValueError):
        AdministrativeArea("", "Amsterdam")


def test_administrative_context_requires_an_area_and_provenance() -> None:
    source = SourceMetadata("PDOK", "CBS", datetime.now(UTC), "CC BY 4.0")
    with pytest.raises(ValueError):
        AdministrativeContext(None, None, None, None, (source,))
    with pytest.raises(ValueError):
        AdministrativeContext(None, None, None, AdministrativeArea("PV27", "NH"), ())
