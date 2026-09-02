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
