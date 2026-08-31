from typing import Protocol

from woonlens.domain.property import PropertyDetails


class PropertyDetailsPort(Protocol):
    """Fetch BAG property details by official addressable-object identifier."""

    async def fetch(self, addressable_object_id: str) -> PropertyDetails: ...
