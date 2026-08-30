from typing import Protocol

from woonlens.domain.addresses import Coordinates
from woonlens.domain.administrative import AdministrativeContext


class AdministrativeContextPort(Protocol):
    """Resolve official areas that contain one coordinate."""

    async def resolve(self, coordinates: Coordinates) -> AdministrativeContext: ...
