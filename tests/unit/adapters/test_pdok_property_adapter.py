from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
import pytest

from woonlens.adapters.sources.pdok.property_client import PdokBagPropertyAdapter
from woonlens.application.errors import (
    PropertyDetailsNotFoundError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)

NOW = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
OBJECT_ID = "0599010000295420"
BUILDING_ID = "1a55ae8d-1fa9-5cc4-85e7-fda7f1e626d2"
BASE_URL = "https://api.test/bag/ogc/v2"


def unit_payload() -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "timeStamp": "2026-08-31T12:00:00Z",
        "numberReturned": 1,
        "features": [
            {
                "type": "Feature",
                "id": "19ab4167-094f-5ece-8da8-55860b77d2a4",
                "properties": {
                    "identificatie": OBJECT_ID,
                    "status": "Verblijfsobject in gebruik",
                    "gebruiksdoel": "onderwijsfunctie,woonfunctie",
                    "oppervlakte": 62,
                    "pand.href": [f"{BASE_URL}/collections/pand/items/{BUILDING_ID}"],
                },
            }
        ],
    }


def building_payload() -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": BUILDING_ID,
        "properties": {
            "identificatie": "0599100000691863",
            "status": "Pand in gebruik",
            "bouwjaar": 1873,
            "gebruiksdoel": "onderwijsfunctie,winkelfunctie,woonfunctie",
            "aantal_verblijfsobjecten": 4,
        },
    }


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def adapter(client: httpx.AsyncClient, *, maximum: int = 10) -> PdokBagPropertyAdapter:
    return PdokBagPropertyAdapter(
        client, BASE_URL, max_related_buildings=maximum, clock=lambda: NOW
    )


@pytest.mark.anyio
async def test_fetches_unit_then_related_building_from_fixed_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.test"
        if request.url.path.endswith("/verblijfsobject/items"):
            assert dict(request.url.params) == {
                "identificatie": OBJECT_ID,
                "limit": "2",
                "f": "json",
            }
            return httpx.Response(200, json=unit_payload())
        assert request.url.path.endswith(f"/pand/items/{BUILDING_ID}")
        assert dict(request.url.params) == {"f": "json"}
        return httpx.Response(200, json=building_payload())

    async with client_for(handler) as client:
        result = await adapter(client).fetch(OBJECT_ID)

    assert result.residential_unit.registered_area_m2 == 62
    assert result.residential_unit.use_purposes == ("onderwijsfunctie", "woonfunctie")
    assert result.buildings[0].id == "0599100000691863"
    assert result.buildings[0].construction_year == 1873
    assert result.source.retrieved_at == NOW


@pytest.mark.anyio
async def test_allows_nullable_fields_and_no_related_building() -> None:
    payload = unit_payload()
    properties = payload["features"][0]["properties"]
    properties.update(
        {
            "status": None,
            "gebruiksdoel": None,
            "oppervlakte": None,
            "pand.href": None,
        }
    )

    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        result = await adapter(client).fetch(OBJECT_ID)

    assert result.residential_unit.use_purposes == ()
    assert result.buildings == ()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "href",
    [
        "https://attacker.test/pand/1a55ae8d-1fa9-5cc4-85e7-fda7f1e626d2",
        f"{BASE_URL}/collections/pand/items/{BUILDING_ID}?secret=true",
    ],
)
async def test_rejects_untrusted_relation_urls(href: str) -> None:
    payload = unit_payload()
    payload["features"][0]["properties"]["pand.href"] = [href]
    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        with pytest.raises(SourceContractError):
            await adapter(client).fetch(OBJECT_ID)


@pytest.mark.anyio
@pytest.mark.parametrize("mutation", ["empty", "duplicate", "wrong_id", "count"])
async def test_rejects_incompatible_unit_contract(mutation: str) -> None:
    payload = deepcopy(unit_payload())
    if mutation == "empty":
        payload["features"] = []
        payload["numberReturned"] = 0
    elif mutation == "duplicate":
        payload["features"].append(payload["features"][0])
        payload["numberReturned"] = 2
    elif mutation == "wrong_id":
        payload["features"][0]["properties"]["identificatie"] = "0" * 16
    else:
        payload["numberReturned"] = 0

    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        error = (
            PropertyDetailsNotFoundError if mutation == "empty" else SourceContractError
        )
        with pytest.raises(error):
            await adapter(client).fetch(OBJECT_ID)


@pytest.mark.anyio
async def test_rejects_more_buildings_than_configured() -> None:
    payload = unit_payload()
    href = f"{BASE_URL}/collections/pand/items/{BUILDING_ID}"
    second = f"{BASE_URL}/collections/pand/items/{UUID(int=2)}"
    payload["features"][0]["properties"]["pand.href"] = [href, second]
    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        with pytest.raises(SourceContractError):
            await adapter(client, maximum=1).fetch(OBJECT_ID)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("handler", "error"),
    [
        (lambda _: httpx.Response(404), PropertyDetailsNotFoundError),
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
