from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from woonlens.adapters.identity.oidc import OidcAccessTokenVerifier
from woonlens.application.errors import AuthenticationError

ISSUER = "https://identity.example"
AUDIENCE = "woonlens-api"


def _token(
    private_key: rsa.RSAPrivateKey,
    *,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    scope: str = "openid woonlens:account",
    expires_delta: timedelta = timedelta(minutes=5),
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": issuer,
            "sub": "opaque-subject",
            "aud": audience,
            "iat": now,
            "exp": now + expires_delta,
            "scope": scope,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def _verifier(public_key: object) -> OidcAccessTokenVerifier:
    return OidcAccessTokenVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url="https://identity.example/jwks",
        required_scope="woonlens:account",
        key_resolver=lambda _: public_key,
    )


@pytest.mark.anyio
async def test_oidc_verifier_returns_only_stable_identity() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    identity = await _verifier(private_key.public_key()).verify(_token(private_key))
    assert identity.issuer == ISSUER
    assert identity.subject == "opaque-subject"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("override", "value"),
    [
        ("issuer", "https://attacker.example"),
        ("audience", "another-api"),
        ("scope", "openid"),
        ("expires_delta", timedelta(minutes=-5)),
    ],
)
async def test_oidc_verifier_rejects_invalid_claims(
    override: str, value: str | timedelta
) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AuthenticationError):
        await _verifier(private_key.public_key()).verify(
            _token(private_key, **{override: value})  # type: ignore[arg-type]
        )


@pytest.mark.anyio
async def test_oidc_verifier_rejects_wrong_signature_and_oversized_token() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = _verifier(other_key.public_key())
    with pytest.raises(AuthenticationError):
        await verifier.verify(_token(private_key))
    with pytest.raises(AuthenticationError):
        await verifier.verify("x" * 8193)
