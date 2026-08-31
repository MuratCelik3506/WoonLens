from typing import Protocol
from uuid import UUID

from woonlens.domain.overview import HomeOverview


class HomeOverviewPort(Protocol):
    async def resolve(self, address_id: UUID) -> HomeOverview: ...
