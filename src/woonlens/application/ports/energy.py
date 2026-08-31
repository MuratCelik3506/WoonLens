from typing import Protocol

from woonlens.domain.energy import EnergyRegistrationDetails


class EnergyRegistrationPort(Protocol):
    """Fetch a current EP-Online registration by trusted BAG object ID."""

    async def fetch(self, bag_object_id: str) -> EnergyRegistrationDetails: ...
