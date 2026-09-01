import asyncio
from collections.abc import Awaitable
from uuid import UUID

from woonlens.application.errors import (
    NeighborhoodContextNotFoundError,
    SourceContractError,
    UnsupportedAddressableObjectError,
    WoonLensError,
)
from woonlens.application.ports.addresses import AddressDetailsPort
from woonlens.application.ports.administrative import AdministrativeContextPort
from woonlens.application.ports.air_quality import AirQualityContextPort
from woonlens.application.ports.energy import EnergyRegistrationPort
from woonlens.application.ports.indicators import NeighborhoodIndicatorsPort
from woonlens.application.ports.property import PropertyDetailsPort
from woonlens.domain.overview import HomeOverview, UnavailableSection


async def _capture[T](
    section: str,
    operation: Awaitable[T],
) -> tuple[T | None, UnavailableSection | None]:
    try:
        return await operation, None
    except WoonLensError as exc:
        return None, UnavailableSection(section, exc.code)


class HomeOverviewService:
    """Compose independent live sources around one trusted address resolution."""

    def __init__(
        self,
        addresses: AddressDetailsPort,
        properties: PropertyDetailsPort,
        energy: EnergyRegistrationPort,
        context: AdministrativeContextPort,
        indicators: NeighborhoodIndicatorsPort,
        air_quality: AirQualityContextPort | None = None,
    ) -> None:
        self._addresses = addresses
        self._properties = properties
        self._energy = energy
        self._context = context
        self._indicators = indicators
        self._air_quality = air_quality

    async def resolve(self, address_id: UUID) -> HomeOverview:
        address = await self._addresses.resolve(address_id)
        if address.addressable_object_type == "Verblijfsobject":
            property_operation = _capture(
                "property", self._properties.fetch(address.addressable_object_id)
            )
            energy_operation = _capture(
                "energy_registration",
                self._energy.fetch(address.addressable_object_id),
            )
        else:
            property_operation = self._unsupported("property")
            energy_operation = self._unsupported("energy_registration")

        air_operation = (
            _capture("air_quality", self._air_quality.resolve(address.coordinates))
            if self._air_quality is not None
            else self._not_configured()
        )
        (
            property_result,
            energy_result,
            context_result,
            air_result,
        ) = await asyncio.gather(
            property_operation,
            energy_operation,
            _capture(
                "administrative_context",
                self._context.resolve(address.coordinates),
            ),
            air_operation,
        )
        property_details, property_failure = property_result
        energy_details, energy_failure = energy_result
        context, context_failure = context_result
        air_quality, air_failure = air_result

        if (
            property_details is not None
            and property_details.residential_unit.id != address.addressable_object_id
        ):
            raise SourceContractError
        if (
            energy_details is not None
            and energy_details.registration.bag_object_id
            != address.addressable_object_id
        ):
            raise SourceContractError

        indicators = None
        indicators_failure = None
        if context is None:
            indicators_failure = UnavailableSection(
                "neighborhood_indicators", "dependency_unavailable"
            )
        elif context.neighborhood is None:
            indicators_failure = UnavailableSection(
                "neighborhood_indicators", NeighborhoodContextNotFoundError.code
            )
        else:
            indicators, indicators_failure = await _capture(
                "neighborhood_indicators",
                self._indicators.fetch(context.neighborhood.code),
            )
            if (
                indicators is not None
                and indicators.neighborhood.code != context.neighborhood.code
            ):
                raise SourceContractError

        failures = tuple(
            failure
            for failure in (
                property_failure,
                energy_failure,
                context_failure,
                indicators_failure,
                air_failure,
            )
            if failure is not None
        )
        return HomeOverview(
            address,
            property_details,
            energy_details,
            context,
            indicators,
            failures,
            air_quality,
        )

    @staticmethod
    async def _unsupported(
        section: str,
    ) -> tuple[None, UnavailableSection]:
        return None, UnavailableSection(section, UnsupportedAddressableObjectError.code)

    @staticmethod
    async def _not_configured() -> tuple[None, None]:
        return None, None
