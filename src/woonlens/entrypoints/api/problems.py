from fastapi import Request
from fastapi.responses import JSONResponse

from woonlens.application.errors import (
    AddressNotFoundError,
    InvalidAddressQueryError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
    WoonLensError,
)

_PROBLEMS: dict[type[WoonLensError], tuple[int, str, str]] = {
    InvalidAddressQueryError: (
        422,
        "Invalid address query",
        "The address query must contain between 2 and 200 characters.",
    ),
    AddressNotFoundError: (
        404,
        "Address not found",
        "The selected official address could not be found.",
    ),
    SourceRateLimitedError: (
        503,
        "Address source temporarily busy",
        "The official address source is temporarily busy. Try again later.",
    ),
    SourceUnavailableError: (
        503,
        "Address source unavailable",
        "The official address source is temporarily unavailable.",
    ),
    SourceContractError: (
        502,
        "Unexpected address source response",
        "The official address source returned an incompatible response.",
    ),
}


async def woonlens_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map typed application errors to safe RFC 9457-style responses."""
    del request
    if not isinstance(exc, WoonLensError):
        raise exc
    status, title, detail = _PROBLEMS.get(
        type(exc),
        (500, "Internal server error", "An unexpected error occurred."),
    )
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://woonlens.nl/problems/{exc.code}",
            "title": title,
            "status": status,
            "detail": detail,
        },
    )
