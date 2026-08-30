from typing import Protocol

from woonlens.domain.indicators import NeighborhoodIndicators


class NeighborhoodIndicatorsPort(Protocol):
    """Fetch selected aggregate indicators for one official neighbourhood."""

    async def fetch(self, neighborhood_code: str) -> NeighborhoodIndicators: ...
