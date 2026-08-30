from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime

import httpx
import pytest

from woonlens.adapters.sources.cbs.statline_client import CbsStatlineIndicatorsAdapter
from woonlens.application.errors import (
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)

NOW = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
NEIGHBORHOOD_CODE = "BU05990112"
MEASURES = {
    "M001642": ("Gemiddelde WOZ-waarde van woningen", "x 1 000 euro"),
    "M000221_2": ("Gemiddelde elektriciteitslevering", "kWh"),
    "M008294": ("Gemiddelde elektriciteitsteruglevering", "kWh"),
    "M000219_2": ("Gemiddeld aardgasverbruik", "m³"),
    "M008297": ("Woningen met zonnestroom", "%"),
}
VALUES = {
    "M001642": 372.0,
    "M000221_2": 1690.0,
    "M008294": 10.0,
    "M000219_2": 140.0,
    "M008297": 1.0,
}


def measure_payload() -> dict[str, object]:
    return {
        "@odata.context": (
            "https://datasets.test/85984NED/$metadata#MeasureCodes"
            "(Identifier,Title,Unit)"
        ),
        "value": [
            {"Identifier": identifier, "Title": title, "Unit": unit}
            for identifier, (title, unit) in MEASURES.items()
        ],
    }


def observation_payload() -> dict[str, object]:
    return {
        "@odata.context": (
            "https://datasets.test/85984NED/$metadata#Observations"
            "(Measure,Value,ValueAttribute,WijkenEnBuurten)"
        ),
        "value": [
            {
                "Measure": measure,
                "Value": value,
                "ValueAttribute": "None",
                "WijkenEnBuurten": NEIGHBORHOOD_CODE,
            }
            for measure, value in VALUES.items()
        ],
    }


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def adapter(client: httpx.AsyncClient) -> CbsStatlineIndicatorsAdapter:
    return CbsStatlineIndicatorsAdapter(
        client,
        "https://datasets.test/odata/v1/CBS/",
        dataset_id="85984NED",
        dataset_year=2024,
        clock=lambda: NOW,
    )


@pytest.mark.anyio
async def test_maps_selected_metrics_and_normalizes_woz() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "datasets.test"
        assert request.url.params["$select"]
        if request.url.path.endswith("/MeasureCodes"):
            assert "M001642" in request.url.params["$filter"]
            return httpx.Response(200, json=measure_payload())
        assert request.url.path.endswith("/Observations")
        assert NEIGHBORHOOD_CODE in request.url.params["$filter"]
        return httpx.Response(200, json=observation_payload())

    async with client_for(handler) as client:
        result = await adapter(client).fetch(NEIGHBORHOOD_CODE)

    by_key = {indicator.key: indicator for indicator in result.indicators}
    assert by_key["average_woz_value"].value == 372000.0
    assert by_key["average_woz_value"].unit == "EUR"
    assert by_key["average_woz_value"].source_unit == "x 1 000 euro"
    assert by_key["homes_with_solar_power"].value == 1.0
    assert result.dataset_year == 2024
    assert result.source.retrieved_at == NOW


@pytest.mark.anyio
async def test_missing_observations_remain_missing_instead_of_zero() -> None:
    observations = observation_payload()
    values = observations["value"]
    assert isinstance(values, list)
    values.pop()
    values[0]["Value"] = None
    values[0]["ValueAttribute"] = "Confidential"

    def handler(request: httpx.Request) -> httpx.Response:
        payload = (
            measure_payload()
            if request.url.path.endswith("MeasureCodes")
            else observations
        )
        return httpx.Response(200, json=payload)

    async with client_for(handler) as client:
        result = await adapter(client).fetch(NEIGHBORHOOD_CODE)

    by_key = {indicator.key: indicator for indicator in result.indicators}
    assert by_key["average_woz_value"].value is None
    assert by_key["average_woz_value"].missing_reason == "Confidential"
    assert by_key["homes_with_solar_power"].value is None
    assert by_key["homes_with_solar_power"].missing_reason == "not_published"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "wrong_code", "wrong_unit", "next_page", "bad_context"],
)
async def test_rejects_incompatible_contracts(mutation: str) -> None:
    measures = deepcopy(measure_payload())
    observations = deepcopy(observation_payload())
    measure_values = measures["value"]
    observation_values = observations["value"]
    assert isinstance(measure_values, list)
    assert isinstance(observation_values, list)
    if mutation == "duplicate":
        observation_values.append(observation_values[0])
    elif mutation == "wrong_code":
        observation_values[0]["WijkenEnBuurten"] = "BU00000000"
    elif mutation == "wrong_unit":
        measure_values[0]["Unit"] = "unknown"
    elif mutation == "next_page":
        observations["@odata.nextLink"] = "https://attacker.test/page"
    else:
        measures["@odata.context"] = "https://datasets.test/other/$metadata"

    def handler(request: httpx.Request) -> httpx.Response:
        payload = (
            measures if request.url.path.endswith("MeasureCodes") else observations
        )
        return httpx.Response(200, json=payload)

    async with client_for(handler) as client:
        with pytest.raises(SourceContractError):
            await adapter(client).fetch(NEIGHBORHOOD_CODE)


@pytest.mark.anyio
async def test_rejects_untrusted_neighborhood_code_before_http() -> None:
    async with client_for(lambda _: pytest.fail("HTTP must not be called")) as client:
        with pytest.raises(SourceContractError):
            await adapter(client).fetch("BU1' or true")


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("handler", "error"),
    [
        (lambda _: httpx.Response(429), SourceRateLimitedError),
        (lambda _: httpx.Response(500), SourceUnavailableError),
        (lambda _: httpx.Response(400), SourceContractError),
        (
            lambda request: (_ for _ in ()).throw(
                httpx.ConnectError("down", request=request)
            ),
            SourceUnavailableError,
        ),
    ],
)
async def test_maps_provider_failures(
    handler: Callable[[httpx.Request], httpx.Response],
    error: type[Exception],
) -> None:
    async with client_for(handler) as client:
        with pytest.raises(error):
            await adapter(client).fetch(NEIGHBORHOOD_CODE)
