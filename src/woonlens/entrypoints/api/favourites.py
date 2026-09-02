from datetime import datetime
from typing import Annotated, Self, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict

from woonlens.application.errors import AccountFeaturesUnavailableError
from woonlens.application.services.favourites import FavouriteService
from woonlens.domain.accounts import ExternalIdentity, FavouriteAddressReference
from woonlens.entrypoints.api.accounts import _identity, _response_headers
from woonlens.entrypoints.api.addresses import ResolvedAddressResponse

router = APIRouter(prefix="/favourites", tags=["favourites"])


class FavouriteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pdok_address_id: UUID


class FavouriteResponse(BaseModel):
    id: UUID
    pdok_address_id: UUID
    created_at: datetime

    @classmethod
    def from_domain(cls, favourite: FavouriteAddressReference) -> Self:
        return cls(
            id=favourite.id,
            pdok_address_id=favourite.pdok_address_id,
            created_at=favourite.created_at,
        )


class FavouritesResponse(BaseModel):
    items: list[FavouriteResponse]


def _service(request: Request) -> FavouriteService:
    service = getattr(request.app.state, "favourite_service", None)
    if service is None:
        raise AccountFeaturesUnavailableError
    return cast(FavouriteService, service)


@router.get("", response_model=FavouritesResponse)
async def list_favourites(
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> FavouritesResponse:
    favourites = await _service(request).list(identity)
    _response_headers(response)
    return FavouritesResponse(
        items=[FavouriteResponse.from_domain(item) for item in favourites]
    )


@router.post("", response_model=FavouriteResponse)
async def add_favourite(
    body: FavouriteCreateRequest,
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> FavouriteResponse:
    favourite = await _service(request).add(identity, body.pdok_address_id)
    _response_headers(response)
    return FavouriteResponse.from_domain(favourite)


@router.delete("/{favourite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favourite(
    favourite_id: UUID,
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> None:
    await _service(request).delete(identity, favourite_id)
    _response_headers(response)


@router.get("/{favourite_id}/address", response_model=ResolvedAddressResponse)
async def resolve_favourite(
    favourite_id: UUID,
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> ResolvedAddressResponse:
    address = await _service(request).resolve(identity, favourite_id)
    _response_headers(response)
    return ResolvedAddressResponse.from_domain(address)
