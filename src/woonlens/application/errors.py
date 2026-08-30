class WoonLensError(Exception):
    """Base class for errors safe to classify at an entrypoint."""

    code = "woonlens_error"


class InvalidAddressQueryError(WoonLensError):
    code = "invalid_address_query"


class AddressNotFoundError(WoonLensError):
    code = "address_not_found"


class SourceRateLimitedError(WoonLensError):
    code = "source_rate_limited"


class SourceUnavailableError(WoonLensError):
    code = "source_unavailable"


class SourceContractError(WoonLensError):
    code = "source_contract_error"
