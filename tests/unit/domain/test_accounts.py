from datetime import UTC, datetime
from uuid import uuid4

import pytest

from woonlens.domain.accounts import Account, ExternalIdentity


def test_external_identity_accepts_https_and_local_development() -> None:
    assert (
        ExternalIdentity("https://identity.example", "subject-1").subject == "subject-1"
    )
    assert ExternalIdentity("http://localhost:8080/realms/test", "subject-2").subject


@pytest.mark.parametrize("issuer", ["http://identity.example", "file:///issuer"])
def test_external_identity_rejects_insecure_non_local_issuer(issuer: str) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        ExternalIdentity(issuer, "subject")


@pytest.mark.parametrize("subject", ["", "x" * 256])
def test_external_identity_rejects_invalid_subject(subject: str) -> None:
    with pytest.raises(ValueError, match="subject"):
        ExternalIdentity("https://identity.example", subject)


def test_account_requires_timezone_aware_creation_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Account(
            id=uuid4(),
            identity=ExternalIdentity("https://identity.example", "subject"),
            created_at=datetime(2026, 9, 2),
        )

    account = Account(
        id=uuid4(),
        identity=ExternalIdentity("https://identity.example", "subject"),
        created_at=datetime(2026, 9, 2, tzinfo=UTC),
    )
    assert account.created_at.tzinfo is UTC
