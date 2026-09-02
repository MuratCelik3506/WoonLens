from datetime import datetime
from typing import Annotated, Self, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from woonlens.application.errors import AccountFeaturesUnavailableError
from woonlens.application.services.comparison import LiveHomeComparisonService
from woonlens.application.services.saved_comparisons import SavedComparisonService
from woonlens.domain.accounts import ExternalIdentity, SavedComparison
from woonlens.entrypoints.api.accounts import _identity, _response_headers
from woonlens.entrypoints.api.comparisons import LiveHomeComparisonResponse

router = APIRouter(prefix="/saved-comparisons", tags=["saved comparisons"])


class SavedComparisonCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    address_ids: list[UUID] = Field(min_length=2, max_length=5)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        result = value.strip()
        if not result:
            raise ValueError("name cannot be blank")
        return result

    @model_validator(mode="after")
    def unique_addresses(self) -> Self:
        if len(set(self.address_ids)) != len(self.address_ids):
            raise ValueError("address_ids must be unique")
        return self


class SavedComparisonRenameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        result = value.strip()
        if not result:
            raise ValueError("name cannot be blank")
        return result


class SavedComparisonResponse(BaseModel):
    id: UUID
    name: str
    address_ids: list[UUID]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, item: SavedComparison) -> Self:
        return cls(
            id=item.id,
            name=item.name,
            address_ids=list(item.address_ids),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class SavedComparisonsResponse(BaseModel):
    items: list[SavedComparisonResponse]


def _service(request: Request) -> SavedComparisonService:
    service = getattr(request.app.state, "saved_comparison_service", None)
    if service is None:
        raise AccountFeaturesUnavailableError
    return cast(SavedComparisonService, service)


@router.get("", response_model=SavedComparisonsResponse)
async def list_saved_comparisons(
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> SavedComparisonsResponse:
    items = await _service(request).list(identity)
    _response_headers(response)
    return SavedComparisonsResponse(
        items=[SavedComparisonResponse.from_domain(item) for item in items]
    )


@router.post("", response_model=SavedComparisonResponse, status_code=201)
async def create_saved_comparison(
    payload: SavedComparisonCreateRequest,
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> SavedComparisonResponse:
    item = await _service(request).create(
        identity, payload.name, tuple(payload.address_ids)
    )
    _response_headers(response)
    return SavedComparisonResponse.from_domain(item)


@router.patch("/{comparison_id}", response_model=SavedComparisonResponse)
async def rename_saved_comparison(
    comparison_id: UUID,
    payload: SavedComparisonRenameRequest,
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> SavedComparisonResponse:
    item = await _service(request).rename(identity, comparison_id, payload.name)
    _response_headers(response)
    return SavedComparisonResponse.from_domain(item)


@router.delete("/{comparison_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_comparison(
    comparison_id: UUID,
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> None:
    await _service(request).delete(identity, comparison_id)
    _response_headers(response)


@router.post("/{comparison_id}/run", response_model=LiveHomeComparisonResponse)
async def run_saved_comparison(
    comparison_id: UUID,
    request: Request,
    response: Response,
    identity: Annotated[ExternalIdentity, Depends(_identity)],
) -> LiveHomeComparisonResponse:
    item = await _service(request).get(identity, comparison_id)
    comparison_service = cast(
        LiveHomeComparisonService, request.app.state.comparison_service
    )
    result = await comparison_service.compare(item.address_ids)
    _response_headers(response)
    return LiveHomeComparisonResponse.from_domain(result)
