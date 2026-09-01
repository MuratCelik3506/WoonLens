from typing import Protocol

from woonlens.domain.addresses import Coordinates
from woonlens.domain.air_quality import AirQualityContext


class AirQualityContextPort(Protocol):
    async def resolve(self, coordinates: Coordinates) -> AirQualityContext: ...
