from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from woonlens.application.errors import AuthenticationError, FavouriteNotFoundError
from woonlens.application.services.accounts import AccountService
from woonlens.domain.accounts import (
    Account,
    ExternalIdentity,
    FavouriteAddressReference,
)
from woonlens.entrypoints.api import create_app

IDENTITY = ExternalIdentity("https://identity.example", "subject")
ACCOUNT = Account(
    UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
    IDENTITY,
    datetime(2026, 9, 2, tzinfo=UTC),
)
FAVOURITE = FavouriteAddressReference(
    UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
    UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
    datetime(2026, 9, 2, tzinfo=UTC),
)


class Verifier:
    async def verify(self, token: str) -> ExternalIdentity:
        if token != "valid":
            raise AuthenticationError
        return IDENTITY


class AccountRepository:
    async def find_by_identity(self, identity: ExternalIdentity) -> Account | None:
        return ACCOUNT

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        return ACCOUNT

    async def delete_by_identity(self, identity: ExternalIdentity) -> bool:
        return True


class FavouriteServiceStub:
    async def list(self, identity: ExternalIdentity):  # type: ignore[no-untyped-def]
        return (FAVOURITE,)

    async def add(self, identity: ExternalIdentity, pdok_address_id: UUID):  # type: ignore[no-untyped-def]
        assert pdok_address_id == FAVOURITE.pdok_address_id
        return FAVOURITE

    async def delete(self, identity: ExternalIdentity, favourite_id: UUID) -> None:
        if favourite_id != FAVOURITE.id:
            raise FavouriteNotFoundError


def test_favourite_endpoints_require_auth_and_reject_provider_fields() -> None:
    app = create_app(
        identity_verifier=Verifier(),
        account_service=AccountService(AccountRepository()),
        favourite_service=FavouriteServiceStub(),  # type: ignore[arg-type]
    )
    headers = {"Authorization": "Bearer valid"}
    with TestClient(app) as client:
        unauthorized = client.get("/api/v1/favourites")
        invalid = client.post(
            "/api/v1/favourites",
            headers=headers,
            json={
                "pdok_address_id": str(FAVOURITE.pdok_address_id),
                "display_name": "Must not persist",
            },
        )
    assert unauthorized.status_code == 401
    assert invalid.status_code == 422


def test_favourite_crud_exposes_only_minimum_reference_fields() -> None:
    app = create_app(
        identity_verifier=Verifier(),
        account_service=AccountService(AccountRepository()),
        favourite_service=FavouriteServiceStub(),  # type: ignore[arg-type]
    )
    headers = {"Authorization": "Bearer valid"}
    with TestClient(app) as client:
        listed = client.get("/api/v1/favourites", headers=headers)
        created = client.post(
            "/api/v1/favourites",
            headers=headers,
            json={"pdok_address_id": str(FAVOURITE.pdok_address_id)},
        )
        deleted = client.delete(f"/api/v1/favourites/{FAVOURITE.id}", headers=headers)
    expected = {
        "id": str(FAVOURITE.id),
        "pdok_address_id": str(FAVOURITE.pdok_address_id),
        "created_at": "2026-09-02T00:00:00Z",
    }
    assert listed.json() == {"items": [expected]}
    assert created.json() == expected
    assert deleted.status_code == 204
    assert "account" not in created.text
    assert created.headers["cache-control"] == "no-store"
