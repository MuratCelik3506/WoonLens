from fastapi import Request
from fastapi.responses import JSONResponse

from woonlens.application.errors import (
    AccountFeaturesUnavailableError,
    AccountNotFoundError,
    AddressNotFoundError,
    AdministrativeContextNotFoundError,
    AuthenticationError,
    EnergyRegistrationNotFoundError,
    FavouriteNotFoundError,
    InvalidAddressQueryError,
    NeighborhoodContextNotFoundError,
    PropertyDetailsNotFoundError,
    SavedComparisonNotFoundError,
    SourceAuthenticationError,
    SourceConfigurationError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
    UnsupportedAddressableObjectError,
    WoonLensError,
)

_PROBLEMS: dict[type[WoonLensError], tuple[int, str, str]] = {
    AuthenticationError: (
        401,
        "Authentication required",
        "A valid account session is required for this request.",
    ),
    AccountFeaturesUnavailableError: (
        503,
        "Account features unavailable",
        "Optional account features are not configured for this deployment.",
    ),
    AccountNotFoundError: (
        404,
        "Account not found",
        "No WoonLens account exists for the authenticated identity.",
    ),
    FavouriteNotFoundError: (
        404,
        "Favourite not found",
        "No favourite address reference exists for this account.",
    ),
    SavedComparisonNotFoundError: (
        404,
        "Saved comparison not found",
        "No saved comparison exists for this account.",
    ),
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
    AdministrativeContextNotFoundError: (
        404,
        "Administrative context not found",
        "No current official administrative context covers the selected address.",
    ),
    NeighborhoodContextNotFoundError: (
        404,
        "Neighbourhood context not found",
        "No official neighbourhood context is available for the selected address.",
    ),
    PropertyDetailsNotFoundError: (
        404,
        "Property details not found",
        "No current official BAG property details are available for the "
        "selected address.",
    ),
    UnsupportedAddressableObjectError: (
        422,
        "Unsupported addressable object",
        "The selected address does not identify a BAG residential unit.",
    ),
    EnergyRegistrationNotFoundError: (
        404,
        "Energy registration not found",
        "No current EP-Online energy registration is available for the "
        "selected address.",
    ),
    SourceConfigurationError: (
        503,
        "Official data source not configured",
        "An official data source is not configured for this deployment.",
    ),
    SourceAuthenticationError: (
        503,
        "Official data source authentication failed",
        "An official data source could not authenticate this deployment.",
    ),
    SourceRateLimitedError: (
        503,
        "Official data source temporarily busy",
        "An official data source is temporarily busy. Try again later.",
    ),
    SourceUnavailableError: (
        503,
        "Official data source unavailable",
        "An official data source is temporarily unavailable.",
    ),
    SourceContractError: (
        502,
        "Unexpected official data response",
        "An official data source returned an incompatible response.",
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
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
        content={
            "type": f"https://woonlens.nl/problems/{exc.code}",
            "title": title,
            "status": status,
            "detail": detail,
        },
    )
