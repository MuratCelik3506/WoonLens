from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from woonlens.application.errors import AuthenticationError
from woonlens.application.services.accounts import AccountService
from woonlens.domain.accounts import (
    Account,
    ExternalIdentity,
    FavouriteAddressReference,
    SavedComparison,
)
from woonlens.entrypoints.api import create_app

IDENTITY = ExternalIdentity("https://identity.example", "subject")
ACCOUNT = Account(
    id=UUID("806f3a79-8ca8-4df4-903f-cbd592fc0a81"),
    identity=IDENTITY,
    created_at=datetime(2026, 9, 2, tzinfo=UTC),
)


class StubVerifier:
    async def verify(self, token: str) -> ExternalIdentity:
        if token != "valid-token":
            raise AuthenticationError
        return IDENTITY


class StubRepository:
    def __init__(self) -> None:
        self.account: Account | None = None

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        assert identity == IDENTITY
        self.account = ACCOUNT
        return ACCOUNT

    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        assert identity == IDENTITY
        return self.account

    async def delete_by_identity(self, identity: ExternalIdentity) -> bool:
        assert identity == IDENTITY
        existed = self.account is not None
        self.account = None
        return existed


class StubFavourites:
    async def list_for_owner(
        self, account_id: UUID
    ) -> tuple[FavouriteAddressReference, ...]:
        assert account_id == ACCOUNT.id
        return (
            FavouriteAddressReference(
                UUID("6820515e-f196-4481-aa23-ace8faf1d070"),
                UUID("e30d6355-d2f1-442f-a073-abe003bec76c"),
                datetime(2026, 9, 2, tzinfo=UTC),
            ),
        )


class StubComparisons:
    async def list_for_owner(self, account_id: UUID) -> tuple[SavedComparison, ...]:
        assert account_id == ACCOUNT.id
        return (
            SavedComparison(
                UUID("aefb6760-e730-44e8-b655-adfd44f21ca0"),
                "Shortlist",
                (
                    UUID("e30d6355-d2f1-442f-a073-abe003bec76c"),
                    UUID("3f439b54-0a81-4d90-acf0-2cdb75fc8626"),
                ),
                datetime(2026, 9, 2, tzinfo=UTC),
                datetime(2026, 9, 2, tzinfo=UTC),
            ),
        )


def test_account_endpoints_require_valid_bearer_authentication() -> None:
    repository = StubRepository()
    app = create_app(
        identity_verifier=StubVerifier(),
        account_service=AccountService(repository),
    )
    with TestClient(app) as client:
        missing = client.get("/api/v1/account")
        invalid = client.get(
            "/api/v1/account", headers={"Authorization": "Bearer invalid"}
        )
    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing.headers["content-type"].startswith("application/problem+json")
    assert missing.headers["www-authenticate"] == "Bearer"


def test_account_endpoints_provision_idempotently_without_exposing_identity() -> None:
    repository = StubRepository()
    app = create_app(
        identity_verifier=StubVerifier(),
        account_service=AccountService(repository),
    )
    headers = {"Authorization": "Bearer valid-token"}
    with TestClient(app) as client:
        before = client.get("/api/v1/account", headers=headers)
        first = client.put("/api/v1/account", headers=headers)
        second = client.put("/api/v1/account", headers=headers)
        current = client.get("/api/v1/account", headers=headers)

    assert before.status_code == 404
    assert first.status_code == second.status_code == current.status_code == 200
    assert first.json() == second.json() == current.json()
    assert first.json() == {
        "id": str(ACCOUNT.id),
        "created_at": "2026-09-02T00:00:00Z",
    }
    assert first.headers["cache-control"] == "no-store"
    assert "issuer" not in first.text
    assert "subject" not in first.text


def test_account_endpoint_is_explicitly_unavailable_without_configuration() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/account", headers={"Authorization": "Bearer token"}
        )
    assert response.status_code == 503


def test_account_export_is_private_and_delete_removes_current_account() -> None:
    repository = StubRepository()
    service = AccountService(repository, StubFavourites(), StubComparisons())  # type: ignore[arg-type]
    app = create_app(identity_verifier=StubVerifier(), account_service=service)
    headers = {"Authorization": "Bearer valid-token"}
    with TestClient(app) as client:
        client.put("/api/v1/account", headers=headers)
        exported = client.get("/api/v1/account/export", headers=headers)
        deleted = client.delete("/api/v1/account", headers=headers)
        missing = client.get("/api/v1/account", headers=headers)

    assert exported.status_code == 200
    assert exported.json()["schema_version"] == "1.0"
    assert exported.json()["saved_comparisons"][0]["address_ids"] == [
        "e30d6355-d2f1-442f-a073-abe003bec76c",
        "3f439b54-0a81-4d90-acf0-2cdb75fc8626",
    ]
    assert "issuer" not in exported.text
    assert "subject" not in exported.text
    assert exported.headers["cache-control"] == "no-store"
    assert deleted.status_code == 204
    assert missing.status_code == 404
