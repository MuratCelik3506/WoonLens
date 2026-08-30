import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from re import fullmatch

import httpx
from pydantic import ValidationError

from woonlens.adapters.sources.cbs.statline_models import (
    MeasureCode,
    MeasureCodeResponse,
    Observation,
    ObservationResponse,
)
from woonlens.application.errors import (
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import SourceMetadata
from woonlens.domain.administrative import AdministrativeArea
from woonlens.domain.indicators import NeighborhoodIndicator, NeighborhoodIndicators


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class _IndicatorDefinition:
    key: str
    measure_id: str
    unit: str
    source_unit: str
    multiplier: float = 1.0


_DEFINITIONS = (
    _IndicatorDefinition("average_woz_value", "M001642", "EUR", "x 1 000 euro", 1000.0),
    _IndicatorDefinition("average_electricity_delivery", "M000221_2", "kWh", "kWh"),
    _IndicatorDefinition("average_electricity_return", "M008294", "kWh", "kWh"),
    _IndicatorDefinition("average_natural_gas_consumption", "M000219_2", "m³", "m³"),
    _IndicatorDefinition("homes_with_solar_power", "M008297", "%", "%"),
)
_MEASURE_IDS = tuple(definition.measure_id for definition in _DEFINITIONS)


def _raise_for_provider_status(response: httpx.Response) -> None:
    if response.status_code == 429:
        raise SourceRateLimitedError
    if response.status_code >= 500:
        raise SourceUnavailableError
    if response.is_error:
        raise SourceContractError


class CbsStatlineIndicatorsAdapter:
    """Fetch a fixed, documented indicator set from CBS StatLine OData."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        *,
        dataset_id: str,
        dataset_year: int,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._dataset_id = dataset_id
        self._dataset_year = dataset_year
        self._clock = clock

    async def fetch(self, neighborhood_code: str) -> NeighborhoodIndicators:
        if fullmatch(r"BU\d{8}", neighborhood_code) is None:
            raise SourceContractError
        measure_filter = " or ".join(
            f"Identifier eq '{measure_id}'" for measure_id in _MEASURE_IDS
        )
        observation_filter = " or ".join(
            f"Measure eq '{measure_id}'" for measure_id in _MEASURE_IDS
        )
        measures_response, observations_response = await asyncio.gather(
            self._get(
                "MeasureCodes",
                {
                    "$filter": measure_filter,
                    "$select": "Identifier,Title,Unit",
                },
            ),
            self._get(
                "Observations",
                {
                    "$filter": (
                        f"WijkenEnBuurten eq '{neighborhood_code}' and "
                        f"({observation_filter})"
                    ),
                    "$select": "Measure,Value,ValueAttribute,WijkenEnBuurten",
                },
            ),
        )
        try:
            measures = MeasureCodeResponse.model_validate(measures_response.json())
            observations = ObservationResponse.model_validate(
                observations_response.json()
            )
        except (ValidationError, ValueError) as exc:
            raise SourceContractError from exc

        self._validate_context(measures.context, "MeasureCodes")
        self._validate_context(observations.context, "Observations")
        if measures.next_link is not None or observations.next_link is not None:
            raise SourceContractError

        measure_by_id = self._unique_by_measure(measures.value)
        observation_by_id = self._unique_by_observation(
            observations.value,
            neighborhood_code,
        )
        if set(measure_by_id) != set(_MEASURE_IDS):
            raise SourceContractError

        indicators = tuple(
            self._map_indicator(
                definition,
                measure_by_id[definition.measure_id],
                observation_by_id.get(definition.measure_id),
            )
            for definition in _DEFINITIONS
        )
        return NeighborhoodIndicators(
            neighborhood=AdministrativeArea(neighborhood_code, neighborhood_code),
            dataset_id=self._dataset_id,
            dataset_year=self._dataset_year,
            indicators=indicators,
            source=SourceMetadata(
                provider="Statistics Netherlands (CBS)",
                dataset=f"Kerncijfers wijken en buurten {self._dataset_year}",
                retrieved_at=self._clock(),
                license_name="CC BY 4.0",
            ),
        )

    async def _get(self, resource: str, params: dict[str, str]) -> httpx.Response:
        try:
            response = await self._client.get(
                f"{self._base_url}/{self._dataset_id}/{resource}",
                params=params,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise SourceUnavailableError from exc
        _raise_for_provider_status(response)
        return response

    def _validate_context(self, context: str, resource: str) -> None:
        expected = f"/{self._dataset_id}/$metadata#{resource}"
        if expected not in context:
            raise SourceContractError

    @staticmethod
    def _unique_by_measure(items: list[MeasureCode]) -> dict[str, MeasureCode]:
        result = {item.identifier: item for item in items}
        if len(result) != len(items) or not set(result).issubset(_MEASURE_IDS):
            raise SourceContractError
        return result

    @staticmethod
    def _unique_by_observation(
        items: list[Observation],
        neighborhood_code: str,
    ) -> dict[str, Observation]:
        result = {item.measure: item for item in items}
        if len(result) != len(items) or not set(result).issubset(_MEASURE_IDS):
            raise SourceContractError
        if any(item.neighborhood_code != neighborhood_code for item in items):
            raise SourceContractError
        return result

    @staticmethod
    def _map_indicator(
        definition: _IndicatorDefinition,
        measure: MeasureCode,
        observation: Observation | None,
    ) -> NeighborhoodIndicator:
        if measure.unit != definition.source_unit:
            raise SourceContractError
        if observation is None:
            value = None
            missing_reason = "not_published"
        elif observation.value is None:
            value = None
            missing_reason = (
                observation.value_attribute
                if observation.value_attribute != "None"
                else "unavailable"
            )
        elif observation.value_attribute != "None":
            raise SourceContractError
        else:
            value = observation.value * definition.multiplier
            missing_reason = None
        return NeighborhoodIndicator(
            key=definition.key,
            measure_id=definition.measure_id,
            label=measure.title,
            value=value,
            unit=definition.unit,
            source_unit=measure.unit,
            missing_reason=missing_reason,
        )
