from typing import Protocol

from woonlens.domain.accounts import ExternalIdentity


class AccessTokenVerifier(Protocol):
    async def verify(self, token: str) -> ExternalIdentity:
        """Verify a bearer credential and return its stable identity."""
