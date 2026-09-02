from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response
from pydantic import BaseModel

from woonlens.application.errors import (
    AccountFeaturesUnavailableError,
    AccountNotFoundError,
    AuthenticationError,
)
from woonlens.application.ports.identity import AccessTokenVerifier
from woonlens.application.services.accounts import AccountService
from woonlens.domain.accounts import ExternalIdentity

router = APIRouter(prefix="/account", tags=["account"])


class AccountResponse(BaseModel):
    id: UUID
    created_at: datetime


class FavouriteExportResponse(BaseModel):
    id: UUID
    pdok_address_id: UUID
    created_at: datetime


class SavedComparisonExportResponse(BaseModel):
    id: UUID
    name: str
    address_ids: tuple[UUID, ...]
    created_at: datetime
    updated_at: datetime


class AccountDataExportResponse(BaseModel):
    schema_version: str = "1.0"
    account: AccountResponse
    favourites: tuple[FavouriteExportResponse, ...]
    saved_comparisons: tuple[SavedComparisonExportResponse, ...]


def _account_dependencies(
    request: Request,
) -> tuple[AccessTokenVerifier, AccountService]:
    verifier = getattr(request.app.state, "identity_verifier", None)
    service = getattr(request.app.state, "account_service", None)
    if verifier is None or service is None:
        raise AccountFeaturesUnavailableError
    return verifier, service


async def _identity(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> ExternalIdentity:
    if authorization is None:
        raise AuthenticationError
    scheme, separator, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or separator != " " or not token:
        raise AuthenticationError
    verifier, _ = _account_dependencies(request)
    return await verifier.verify(token)


def _response_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Authorization"


@router.put("", response_model=AccountResponse)
async def ensure_account(
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> AccountResponse:
    """Idempotently provision the minimum account for a verified identity."""
    _, service = _account_dependencies(request)
    account = await service.ensure_account(identity)
    _response_headers(response)
    return AccountResponse(id=account.id, created_at=account.created_at)


@router.get("", response_model=AccountResponse)
async def current_account(
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> AccountResponse:
    """Return the current verified identity's application account."""
    _, service = _account_dependencies(request)
    account = await service.current_account(identity)
    if account is None:
        raise AccountNotFoundError
    _response_headers(response)
    return AccountResponse(id=account.id, created_at=account.created_at)


@router.get("/export", response_model=AccountDataExportResponse)
async def export_account_data(
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> AccountDataExportResponse:
    """Export only the current account's application-owned data."""
    _, service = _account_dependencies(request)
    snapshot = await service.export_data(identity)
    _response_headers(response)
    return AccountDataExportResponse(
        account=AccountResponse(
            id=snapshot.account.id, created_at=snapshot.account.created_at
        ),
        favourites=tuple(
            FavouriteExportResponse(
                id=item.id,
                pdok_address_id=item.pdok_address_id,
                created_at=item.created_at,
            )
            for item in snapshot.favourites
        ),
        saved_comparisons=tuple(
            SavedComparisonExportResponse(
                id=item.id,
                name=item.name,
                address_ids=item.address_ids,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in snapshot.saved_comparisons
        ),
    )


@router.delete("", status_code=204)
async def delete_account(
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> None:
    """Delete the current WoonLens account without touching its OIDC identity."""
    _, service = _account_dependencies(request)
    await service.delete_account(identity)
    _response_headers(response)
