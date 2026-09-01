from datetime import UTC, datetime

import httpx
import pytest

from woonlens.adapters.sources.luchtmeetnet.client import (
    LuchtmeetnetAirQualityAdapter,
    _latest_measurement,
    _parse_components,
    _parse_locations,
    _parse_series,
)
from woonlens.application.errors import (
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import Coordinates

LOCATIONS = """# export
meetlocatie_id;bron_id;meetlocatie_naam;meetlocatie_plaatsnaam;breedtegraad;lengtegraad;hoogte;meetlocatie_begindatumtijd;meetlocatie_einddatumtijd
NL00001;LML;Near NO2;City;52.0000;4.0000;1;2020-01-01T00:00:00+01:00;
NL00002;DCMR;Near particles;City;52.0100;4.0100;1;2020-01-01T00:00:00+01:00;
NL00003;LML;Far PM25;City;52.1000;4.1000;1;2020-01-01T00:00:00+01:00;
NL00999;LML;Ended;City;52.0000;4.0000;1;2000-01-01T00:00:00+01:00;2010-01-01T00:00:00+01:00
"""

SERIES = """# export
meetreeks_id;meetlocatie_id;component;matrix;meetreeks_begindatumtijd;meetreeks_einddatumtijd;gebiedstype;stationstype;meethoogte
one;NL00001;NO2;lucht;2020-01-01T00:00:00+01:00;;stad;verkeer;2
two;NL00002;NO2;lucht;2020-01-01T00:00:00+01:00;;stad;achtergrond;2
three;NL00002;PM10;lucht;2020-01-01T00:00:00+01:00;;stad;achtergrond;2
four;NL00003;PM2.5;lucht;2020-01-01T00:00:00+01:00;;regionaal;achtergrond;2
ended;NL00001;PM10;lucht;2010-01-01T00:00:00+01:00;2020-01-01T00:00:00+01:00;stad;verkeer;2
rain;NL00001;PM2.5;regen;2020-01-01T00:00:00+01:00;;stad;verkeer;2
"""

COMPONENTS = """# export
component;matrix;component_naam;comp_matrix_naam;comp_matrix_eenheid
NO2;lucht;stikstofdioxide;stikstofdioxide (lucht);µg/m³
PM10;lucht;fijn stof PM10;fijn stof PM10 (lucht);µg/m³
PM2.5;lucht;fijn stof PM2.5;fijn stof PM2.5 (lucht);µg/m³
"""


def _measurement(formula: str, value: float) -> dict[str, object]:
    return {
        "formula": formula,
        "value": value,
        "timestamp_measured_start": "2026-09-01T07:00:00+00:00",
        "timestamp_measured_end": "2026-09-01T08:00:00+00:00",
    }


@pytest.mark.anyio
async def test_selects_nearest_compatible_stations_and_maps_latest_readings() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        name = request.url.path.rsplit("/", 1)[-1]
        if name == "luchtmeetnet_meetlocaties.csv":
            return httpx.Response(200, text=LOCATIONS)
        if name == "luchtmeetnet_meetreeksen.csv":
            return httpx.Response(200, text=SERIES)
        if name == "luchtmeetnet_componenten.csv":
            return httpx.Response(200, text=COMPONENTS)
        station_id = request.url.path.split("/")[-2]
        rows = {
            "NL00001": [_measurement("NO2", 12.0)],
            "NL00002": [
                _measurement("PM10", 18.5),
                _measurement("NO2", 99.0),
            ],
            "NL00003": [
                _measurement("PM25", 7.25),
                {**_measurement("PM25", 1.0), "value": None},
            ],
        }[station_id]
        return httpx.Response(200, json={"pagination": {}, "data": rows})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = LuchtmeetnetAirQualityAdapter(
            client,
            "https://api.example/open_api",
            "https://data.example/Metadata",
            clock=lambda: datetime(2026, 9, 1, 8, 5, tzinfo=UTC),
        )
        result = await adapter.resolve(Coordinates(4.0001, 52.0001))

    by_pollutant = {item.pollutant: item for item in result.observations}
    assert result.missing_pollutants == ()
    assert by_pollutant["NO2"].station.id == "NL00001"
    assert by_pollutant["NO2"].station.station_type == "verkeer"
    assert by_pollutant["PM10"].station.id == "NL00002"
    assert by_pollutant["PM2.5"].station.id == "NL00003"
    assert by_pollutant["PM2.5"].value == 7.25
    assert by_pollutant["PM2.5"].unit == "µg/m³"
    assert by_pollutant["PM2.5"].scope == "monitoring-station"
    assert by_pollutant["PM2.5"].status == "current-unratified"
    assert by_pollutant["NO2"].station.distance_km < 0.1
    assert result.source.provider == "Luchtmeetnet / RIVM"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status", "error"),
    [
        (429, SourceRateLimitedError),
        (503, SourceUnavailableError),
        (400, SourceContractError),
    ],
)
async def test_classifies_provider_status(status: int, error: type[Exception]) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(status)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = LuchtmeetnetAirQualityAdapter(
            client, "https://api.example", "https://data.example"
        )
        with pytest.raises(error):
            await adapter.resolve(Coordinates(4.0, 52.0))


@pytest.mark.anyio
async def test_classifies_network_failure() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = LuchtmeetnetAirQualityAdapter(
            client, "https://api.example", "https://data.example"
        )
        with pytest.raises(SourceUnavailableError):
            await adapter.resolve(Coordinates(4.0, 52.0))


def test_rejects_invalid_metadata_and_measurements() -> None:
    with pytest.raises(SourceContractError):
        _parse_locations("wrong;header\nvalue;value")
    with pytest.raises(SourceContractError):
        _parse_series("wrong;header\nvalue;value")
    with pytest.raises(SourceContractError):
        _parse_components(COMPONENTS.replace("PM2.5;", "OTHER;"))
    with pytest.raises(SourceContractError):
        _latest_measurement(
            [{"formula": "NO2", "value": "bad", "timestamp_measured_start": "x"}],
            "NO2",
        )
    assert _latest_measurement([], "NO2") is None
