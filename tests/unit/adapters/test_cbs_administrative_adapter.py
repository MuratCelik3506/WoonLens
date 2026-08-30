from collections.abc import Callable
from copy import deepcopy

import httpx
import pytest

from woonlens.adapters.sources.cbs.client import CbsAdministrativeContextAdapter
from woonlens.application.errors import (
    AdministrativeContextNotFoundError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)
from woonlens.domain.addresses import Coordinates


def neighborhood_payload() -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "timeStamp": "2026-08-30T12:00:00Z",
        "numberReturned": 1,
        "features": [
            {
                "type": "Feature",
                "id": "11111111-1111-4111-8111-111111111111",
                "properties": {
                    "bu_code": "BU0363AF08",
                    "bu_naam": "Zuiderkerkbuurt",
                    "wk_code": "WK0363AF",
                    "wk_naam": "Nieuwmarkt/Lastage",
                    "gm_code": "GM0363",
                    "gm_naam": "Amsterdam",
                    "jaar": "2026",
                },
                "geometry": {"provider_specific": True},
            }
        ],
    }


def province_payload() -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "timeStamp": "2026-08-30T12:00:01Z",
        "numberReturned": 1,
        "features": [
            {
                "type": "Feature",
                "id": "22222222-2222-4222-8222-222222222222",
                "properties": {
                    "statcode": "PV27",
                    "statnaam": "Noord-Holland",
                    "jaarcode": 2026,
                    "rubriek": "provincie",
                },
            }
        ],
    }


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.anyio
async def test_maps_current_official_areas_and_uses_configured_urls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "provider.test"
        assert request.url.params["limit"] == "2"
        assert request.url.params["bbox"].count(",") == 3
        if request.url.path.endswith("/collections/buurten/items"):
            return httpx.Response(200, json=neighborhood_payload())
        assert request.url.path.endswith("/collections/provincie_gegeneraliseerd/items")
        assert request.url.params["jaarcode"] == "2026"
        return httpx.Response(200, json=province_payload())

    async with client_for(handler) as client:
        result = await CbsAdministrativeContextAdapter(
            client,
            "https://provider.test/neighborhoods/",
            "https://provider.test/regions/",
            dataset_year=2026,
        ).resolve(Coordinates(4.9, 52.37))

    assert result.neighborhood is not None
    assert result.neighborhood.code == "BU0363AF08"
    assert result.district is not None
    assert result.municipality is not None
    assert result.province is not None
    assert result.province.name == "Noord-Holland"
    assert len(result.sources) == 2


@pytest.mark.anyio
async def test_accepts_partial_coverage() -> None:
    empty = neighborhood_payload()
    empty["numberReturned"] = 0
    empty["features"] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = empty if "buurten" in request.url.path else province_payload()
        return httpx.Response(200, json=payload)

    async with client_for(handler) as client:
        result = await CbsAdministrativeContextAdapter(
            client,
            "https://provider.test/neighborhoods",
            "https://provider.test/regions",
            dataset_year=2026,
        ).resolve(Coordinates(4.9, 52.37))

    assert result.neighborhood is None
    assert result.province is not None
    assert len(result.sources) == 1


@pytest.mark.anyio
async def test_rejects_no_coverage() -> None:
    empty_neighborhood = neighborhood_payload()
    empty_neighborhood["numberReturned"] = 0
    empty_neighborhood["features"] = []
    empty_province = province_payload()
    empty_province["numberReturned"] = 0
    empty_province["features"] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = (
            empty_neighborhood if "buurten" in request.url.path else empty_province
        )
        return httpx.Response(200, json=payload)

    async with client_for(handler) as client:
        with pytest.raises(AdministrativeContextNotFoundError):
            await CbsAdministrativeContextAdapter(
                client,
                "https://provider.test/neighborhoods",
                "https://provider.test/regions",
                dataset_year=2026,
            ).resolve(Coordinates(4.9, 52.37))


@pytest.mark.anyio
@pytest.mark.parametrize("invalid", ["count", "year", "payload"])
async def test_rejects_incompatible_provider_responses(invalid: str) -> None:
    neighborhood = deepcopy(neighborhood_payload())
    if invalid == "count":
        neighborhood["numberReturned"] = 2
    elif invalid == "year":
        features = neighborhood["features"]
        assert isinstance(features, list)
        features[0]["properties"]["jaar"] = "2025"
    else:
        neighborhood = {"unexpected": True}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = neighborhood if "buurten" in request.url.path else province_payload()
        return httpx.Response(200, json=payload)

    async with client_for(handler) as client:
        with pytest.raises(SourceContractError):
            await CbsAdministrativeContextAdapter(
                client,
                "https://provider.test/neighborhoods",
                "https://provider.test/regions",
                dataset_year=2026,
            ).resolve(Coordinates(4.9, 52.37))


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("handler", "error"),
    [
        (lambda _: httpx.Response(429), SourceRateLimitedError),
        (lambda _: httpx.Response(500), SourceUnavailableError),
        (lambda _: httpx.Response(400), SourceContractError),
        (
            lambda request: (_ for _ in ()).throw(
                httpx.ReadTimeout("slow", request=request)
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
            await CbsAdministrativeContextAdapter(
                client,
                "https://provider.test/neighborhoods",
                "https://provider.test/regions",
                dataset_year=2026,
            ).resolve(Coordinates(4.9, 52.37))
