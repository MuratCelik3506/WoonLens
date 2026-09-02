from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from fastapi.testclient import TestClient

from woonlens.application.errors import AuthenticationError
from woonlens.application.services.accounts import AccountService
from woonlens.application.services.saved_comparisons import SavedComparisonService
from woonlens.domain.accounts import Account, ExternalIdentity, SavedComparison
from woonlens.entrypoints.api import create_app

IDENTITY = ExternalIdentity("https://identity.example", "subject")
NOW = datetime(2026, 9, 2, tzinfo=UTC)
IDS = ["cccccccc-cccc-4ccc-8ccc-cccccccccccc", "dddddddd-dddd-4ddd-8ddd-dddddddddddd"]
ITEM = SavedComparison(
    UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
    "Shortlist",
    tuple(UUID(item) for item in IDS),
    NOW,
    NOW,
)


class Verifier:
    async def verify(self, token: str) -> ExternalIdentity:
        if token != "valid":
            raise AuthenticationError
        return IDENTITY


class Accounts:
    async def find_by_identity(self, identity: ExternalIdentity) -> Account:
        return Account(UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"), identity, NOW)

    async def get_or_create(self, identity: ExternalIdentity) -> Account:
        return await self.find_by_identity(identity)

    async def delete_by_identity(self, identity: ExternalIdentity) -> bool:
        return True


class Service:
    async def list(self, identity: ExternalIdentity) -> tuple[SavedComparison, ...]:
        return (ITEM,)

    async def create(
        self, identity: ExternalIdentity, name: str, address_ids: tuple[UUID, ...]
    ) -> SavedComparison:
        return SavedComparison(ITEM.id, name, address_ids, NOW, NOW)

    async def rename(
        self, identity: ExternalIdentity, comparison_id: UUID, name: str
    ) -> SavedComparison:
        return SavedComparison(ITEM.id, name, ITEM.address_ids, NOW, NOW)

    async def delete(self, identity: ExternalIdentity, comparison_id: UUID) -> None:
        return None


def test_saved_comparison_crud_and_validation() -> None:
    app = create_app(
        identity_verifier=Verifier(),
        account_service=AccountService(Accounts()),
        saved_comparison_service=cast(SavedComparisonService, Service()),
    )
    headers = {"Authorization": "Bearer valid"}
    with TestClient(app) as client:
        unauthorized = client.get("/api/v1/saved-comparisons")
        listed = client.get("/api/v1/saved-comparisons", headers=headers)
        created = client.post(
            "/api/v1/saved-comparisons",
            headers=headers,
            json={"name": "  Shortlist  ", "address_ids": IDS},
        )
        renamed = client.patch(
            f"/api/v1/saved-comparisons/{ITEM.id}",
            headers=headers,
            json={"name": "Finalists"},
        )
        deleted = client.delete(f"/api/v1/saved-comparisons/{ITEM.id}", headers=headers)
        duplicate = client.post(
            "/api/v1/saved-comparisons",
            headers=headers,
            json={"name": "Bad", "address_ids": [IDS[0], IDS[0]]},
        )
        facts = client.post(
            "/api/v1/saved-comparisons",
            headers=headers,
            json={"name": "Bad", "address_ids": IDS, "display_names": ["forbidden"]},
        )
    assert unauthorized.status_code == 401
    assert listed.json()["items"][0]["address_ids"] == IDS
    assert created.status_code == 201 and created.json()["name"] == "Shortlist"
    assert renamed.json()["name"] == "Finalists"
    assert deleted.status_code == 204
    assert duplicate.status_code == facts.status_code == 422
    assert "account" not in listed.text
