class WoonLensError(Exception):
    """Base class for errors safe to classify at an entrypoint."""

    code = "woonlens_error"


class AuthenticationError(WoonLensError):
    """The supplied authentication credential is missing or invalid."""

    code = "authentication_failed"


class AccountFeaturesUnavailableError(WoonLensError):
    code = "account_features_unavailable"


class AccountNotFoundError(WoonLensError):
    code = "account_not_found"


class InvalidAddressQueryError(WoonLensError):
    code = "invalid_address_query"


class AddressNotFoundError(WoonLensError):
    code = "address_not_found"


class AdministrativeContextNotFoundError(WoonLensError):
    code = "administrative_context_not_found"


class NeighborhoodContextNotFoundError(WoonLensError):
    code = "neighborhood_context_not_found"


class PropertyDetailsNotFoundError(WoonLensError):
    code = "property_details_not_found"


class UnsupportedAddressableObjectError(WoonLensError):
    code = "unsupported_addressable_object"


class EnergyRegistrationNotFoundError(WoonLensError):
    code = "energy_registration_not_found"


class SourceConfigurationError(WoonLensError):
    code = "source_configuration_error"


class SourceAuthenticationError(WoonLensError):
    code = "source_authentication_error"


class SourceRateLimitedError(WoonLensError):
    code = "source_rate_limited"


class SourceUnavailableError(WoonLensError):
    code = "source_unavailable"


class SourceContractError(WoonLensError):
    code = "source_contract_error"
