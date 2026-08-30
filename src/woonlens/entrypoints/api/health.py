from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    """Public readiness response without configuration details."""

    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report whether the API process is ready to receive requests."""
    return HealthResponse()
