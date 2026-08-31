from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from woonlens.adapters.sources.ep_online.client import EpOnlineEnergyRegistrationAdapter
from woonlens.application.errors import (
    EnergyRegistrationNotFoundError,
    SourceAuthenticationError,
    SourceConfigurationError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)

NOW = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
OBJECT_ID = "0599010000295420"
BASE_URL = "https://energy.test/api/v5"


def record(
    *, registered: str = "2026-02-04T15:31:59.943", valid: str = "2036-01-14T00:00:00"
) -> dict[str, Any]:
    return {
        "Registratiedatum": registered,
        "Opnamedatum": "2026-01-14T00:00:00",
        "Geldig_tot": valid,
        "Soort_opname": "Basisopname",
        "Status": "Bestaand",
        "Gebouwklasse": "Woningbouw",
        "Gebouwtype": "Appartement",
        "Gebouwsubtype": "Tussenmidden",
        "BAGVerblijfsobjectID": OBJECT_ID,
        "BAGPandIDs": ["0599100000691863"],
        "Bouwjaar": 1873,
        "Gebruiksoppervlakte_thermische_zone": 54.41,
        "Energieklasse": "B",
        "Energiebehoefte": 109.02,
        "PrimaireFossieleEnergie": 172.52,
        "Aandeel_hernieuwbare_energie": 0.0,
        "BerekendeCO2Emissie": 31.8,
        "BerekendeEnergieverbruik": 172.51,
    }


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def adapter(
    client: httpx.AsyncClient, key: str | None = "secret"
) -> EpOnlineEnergyRegistrationAdapter:
    return EpOnlineEnergyRegistrationAdapter(client, BASE_URL, key, clock=lambda: NOW)


@pytest.mark.anyio
async def test_maps_current_registration_without_exposing_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert (
            request.url
            == f"{BASE_URL}/PandEnergielabel/AdresseerbaarObject/{OBJECT_ID}"
        )
        assert request.headers["Authorization"] == "secret"
        assert "secret" not in str(request.url)
        return httpx.Response(200, json=[record()])

    async with client_for(handler) as client:
        result = await adapter(client).fetch(OBJECT_ID)

    assert result.registration.energy_class == "B"
    assert result.registration.thermal_zone_area_m2 == 54.41
    assert result.registration.bag_building_ids == ("0599100000691863",)
    assert result.source.retrieved_at == NOW


@pytest.mark.anyio
async def test_selects_latest_non_expired_registration() -> None:
    payload = [
        record(registered="2025-01-01", valid="2026-01-01"),
        record(registered="2024-01-01", valid="2030-01-01"),
        record(registered="2026-01-01", valid="2032-01-01"),
    ]
    payload[1]["Energieklasse"] = "C"
    payload[2]["Energieklasse"] = "A"
    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        result = await adapter(client).fetch(OBJECT_ID)
    assert result.registration.energy_class == "A"


@pytest.mark.anyio
@pytest.mark.parametrize("payload", [[], [record(valid="2020-01-01")]])
async def test_missing_current_registration(payload: list[dict[str, Any]]) -> None:
    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        with pytest.raises(EnergyRegistrationNotFoundError):
            await adapter(client).fetch(OBJECT_ID)


@pytest.mark.anyio
async def test_rejects_mismatched_bag_identifier() -> None:
    payload = deepcopy(record())
    payload["BAGVerblijfsobjectID"] = "1" * 16
    async with client_for(lambda _: httpx.Response(200, json=[payload])) as client:
        with pytest.raises(SourceContractError):
            await adapter(client).fetch(OBJECT_ID)


@pytest.mark.anyio
@pytest.mark.parametrize("bag_id", ["invalid", "0000000000000000"])
async def test_rejects_untrusted_identifier_before_http(bag_id: str) -> None:
    async with client_for(lambda _: pytest.fail("HTTP must not be called")) as client:
        with pytest.raises(SourceContractError):
            await adapter(client).fetch(bag_id)


@pytest.mark.anyio
async def test_missing_key_fails_before_http() -> None:
    async with client_for(lambda _: pytest.fail("HTTP must not be called")) as client:
        with pytest.raises(SourceConfigurationError):
            await adapter(client, None).fetch(OBJECT_ID)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("handler", "error"),
    [
        (lambda _: httpx.Response(401), SourceAuthenticationError),
        (lambda _: httpx.Response(403), SourceAuthenticationError),
        (lambda _: httpx.Response(404), EnergyRegistrationNotFoundError),
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
    handler: Callable[[httpx.Request], httpx.Response], error: type[Exception]
) -> None:
    async with client_for(handler) as client:
        with pytest.raises(error):
            await adapter(client).fetch(OBJECT_ID)
