import asyncio
import csv
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
from math import asin, cos, radians, sin, sqrt
from typing import Any

import httpx

from woonlens.application.errors import (
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import Coordinates, SourceMetadata
from woonlens.domain.air_quality import (
    AirQualityContext,
    AirQualityObservation,
    MonitoringStation,
)

POLLUTANTS = ("NO2", "PM10", "PM2.5")
API_FORMULAS = {"NO2": "NO2", "PM10": "PM10", "PM2.5": "PM25"}
LIMITATION = (
    "These are recent unratified observations at nearby monitoring stations, "
    "not measurements at the selected address or health conclusions. Station "
    "type, distance, weather, and local conditions affect representativeness."
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class _Location:
    id: str
    name: str
    operator: str
    coordinates: Coordinates


@dataclass(frozen=True, slots=True)
class _Series:
    station_id: str
    pollutant: str
    station_type: str


class LuchtmeetnetAirQualityAdapter:
    def __init__(
        self,
        client: httpx.AsyncClient,
        api_url: str,
        metadata_url: str,
        *,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._client = client
        self._api_url = api_url.rstrip("/")
        self._metadata_url = metadata_url.rstrip("/")
        self._clock = clock

    async def resolve(self, coordinates: Coordinates) -> AirQualityContext:
        locations_response, series_response, components_response = await asyncio.gather(
            self._get_metadata("luchtmeetnet_meetlocaties.csv"),
            self._get_metadata("luchtmeetnet_meetreeksen.csv"),
            self._get_metadata("luchtmeetnet_componenten.csv"),
        )
        locations = _parse_locations(locations_response.text)
        series = _parse_series(series_response.text)
        components = _parse_components(components_response.text)
        selected = _select_stations(coordinates, locations, series)

        station_ids = sorted({item[0].id for item in selected.values()})
        measurements = await asyncio.gather(
            *(self._get_measurements(station_id) for station_id in station_ids)
        )
        rows_by_station = dict(zip(station_ids, measurements, strict=True))
        observations: list[AirQualityObservation] = []
        missing: list[str] = []
        for pollutant in POLLUTANTS:
            station_and_type = selected.get(pollutant)
            if station_and_type is None:
                missing.append(pollutant)
                continue
            location, station_type, distance = station_and_type
            measurement = _latest_measurement(
                rows_by_station[location.id], API_FORMULAS[pollutant]
            )
            if measurement is None:
                missing.append(pollutant)
                continue
            observations.append(
                AirQualityObservation(
                    pollutant=pollutant,
                    label=components[pollutant][0],
                    value=measurement[0],
                    unit=components[pollutant][1],
                    measured_from=measurement[1],
                    measured_until=measurement[2],
                    station=MonitoringStation(
                        location.id,
                        location.name,
                        location.operator,
                        station_type,
                        location.coordinates,
                        round(distance, 3),
                    ),
                )
            )
        return AirQualityContext(
            tuple(observations),
            tuple(missing),
            SourceMetadata(
                "Luchtmeetnet / RIVM",
                "Open API and Luchtmeetnet metadata",
                self._clock(),
                "Terms require per-dataset verification",
            ),
            LIMITATION,
        )

    async def _get_metadata(self, filename: str) -> httpx.Response:
        return await self._get(f"{self._metadata_url}/{filename}")

    async def _get_measurements(self, station_id: str) -> list[dict[str, Any]]:
        response = await self._get(
            f"{self._api_url}/stations/{station_id}/measurements",
            params={"page": "1", "order_by": "timestamp_measured"},
        )
        try:
            payload = response.json()
            data = payload["data"]
            if not isinstance(data, list):
                raise TypeError
            return data
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceContractError from exc

    async def _get(
        self, url: str, params: dict[str, str] | None = None
    ) -> httpx.Response:
        try:
            response = await self._client.get(url, params=params)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise SourceUnavailableError from exc
        if response.status_code == 429:
            raise SourceRateLimitedError
        if response.status_code >= 500:
            raise SourceUnavailableError
        if response.is_error:
            raise SourceContractError
        return response


def _csv_rows(text: str) -> list[dict[str, str]]:
    content = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    try:
        return list(csv.DictReader(StringIO(content), delimiter=";"))
    except csv.Error as exc:
        raise SourceContractError from exc


def _parse_locations(text: str) -> dict[str, _Location]:
    result: dict[str, _Location] = {}
    try:
        for row in _csv_rows(text):
            if row["meetlocatie_einddatumtijd"]:
                continue
            station_id = row["meetlocatie_id"]
            result[station_id] = _Location(
                station_id,
                row["meetlocatie_naam"] or row["meetlocatie_plaatsnaam"],
                row["bron_id"],
                Coordinates(float(row["lengtegraad"]), float(row["breedtegraad"])),
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceContractError from exc
    if not result:
        raise SourceContractError
    return result


def _parse_series(text: str) -> tuple[_Series, ...]:
    result: list[_Series] = []
    try:
        for row in _csv_rows(text):
            if (
                row["meetreeks_einddatumtijd"]
                or row["matrix"] != "lucht"
                or row["component"] not in POLLUTANTS
            ):
                continue
            result.append(
                _Series(
                    row["meetlocatie_id"],
                    row["component"],
                    row["stationstype"] or "unknown",
                )
            )
    except (KeyError, TypeError) as exc:
        raise SourceContractError from exc
    if not result:
        raise SourceContractError
    return tuple(result)


def _parse_components(text: str) -> dict[str, tuple[str, str]]:
    try:
        result = {
            row["component"]: (row["component_naam"], row["comp_matrix_eenheid"])
            for row in _csv_rows(text)
            if row["component"] in POLLUTANTS and row["matrix"] == "lucht"
        }
    except (KeyError, TypeError) as exc:
        raise SourceContractError from exc
    if set(result) != set(POLLUTANTS) or any(
        not all(value) for value in result.values()
    ):
        raise SourceContractError
    return result


def _select_stations(
    address: Coordinates,
    locations: dict[str, _Location],
    series: tuple[_Series, ...],
) -> dict[str, tuple[_Location, str, float]]:
    selected: dict[str, tuple[_Location, str, float]] = {}
    for item in series:
        location = locations.get(item.station_id)
        if location is None:
            continue
        distance = _haversine_km(address, location.coordinates)
        current = selected.get(item.pollutant)
        if current is None or distance < current[2]:
            selected[item.pollutant] = (location, item.station_type, distance)
    return selected


def _haversine_km(first: Coordinates, second: Coordinates) -> float:
    latitude_delta = radians(second.latitude - first.latitude)
    longitude_delta = radians(second.longitude - first.longitude)
    value = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(first.latitude))
        * cos(radians(second.latitude))
        * sin(longitude_delta / 2) ** 2
    )
    return 6371.0088 * 2 * asin(sqrt(value))


def _latest_measurement(
    rows: list[dict[str, Any]], formula: str
) -> tuple[float, datetime, datetime] | None:
    matches: list[tuple[float, datetime, datetime]] = []
    try:
        for row in rows:
            if row.get("formula") != formula or row.get("value") is None:
                continue
            matches.append(
                (
                    float(row["value"]),
                    datetime.fromisoformat(row["timestamp_measured_start"]),
                    datetime.fromisoformat(row["timestamp_measured_end"]),
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceContractError from exc
    return max(matches, key=lambda item: item[2]) if matches else None
