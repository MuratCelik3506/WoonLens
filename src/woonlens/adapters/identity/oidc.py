import asyncio
from collections.abc import Callable
from typing import Any

import jwt
from jwt import PyJWKClient, PyJWTError

from woonlens.application.errors import AuthenticationError
from woonlens.domain.accounts import ExternalIdentity


class OidcAccessTokenVerifier:
    """Verify asymmetric OIDC access tokens against an allow-listed issuer."""

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        required_scope: str,
        algorithms: tuple[str, ...] = ("RS256",),
        key_resolver: Callable[[str], Any] | None = None,
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._required_scope = required_scope
        self._algorithms = algorithms
        jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=300)
        self._key_resolver = key_resolver or jwks_client.get_signing_key_from_jwt

    async def verify(self, token: str) -> ExternalIdentity:
        if not token or len(token) > 8192:
            raise AuthenticationError
        try:
            signing_key = await asyncio.to_thread(self._key_resolver, token)
            claims = jwt.decode(
                token,
                getattr(signing_key, "key", signing_key),
                algorithms=list(self._algorithms),
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["iss", "sub", "aud", "exp", "iat"]},
                leeway=30,
            )
            issuer = claims["iss"]
            subject = claims["sub"]
            scope = claims.get("scope", "")
            scopes = scope.split() if isinstance(scope, str) else []
            if (
                not isinstance(issuer, str)
                or not isinstance(subject, str)
                or self._required_scope not in scopes
            ):
                raise AuthenticationError
            return ExternalIdentity(issuer=issuer, subject=subject)
        except (PyJWTError, KeyError, TypeError, ValueError) as exc:
            raise AuthenticationError from exc
