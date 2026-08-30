from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest

from woonlens.adapters.sources.pdok.client import (
    PdokBagAddressAdapter,
    PdokLocationSearchAdapter,
)
from woonlens.application.errors import (
    AddressNotFoundError,
    SourceContractError,
    SourceRateLimitedError,
    SourceUnavailableError,
)

ADDRESS_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_ID = UUID("22222222-2222-4222-8222-222222222222")
RETRIEVED_AT = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


def search_payload(*, count: int = 1) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "timeStamp": "2026-08-30T12:00:00Z",
        "numberReturned": count,
        "features": [
            {
                "type": "Feature",
                "id": str(ADDRESS_ID),
                "properties": {
                    "collection_id": "adres",
                    "collection_version": 1,
                    "display_name": "Examplelaan 10, 1234AB Teststad",
                    "ignored_new_field": True,
                },
                "geometry": {"type": "Point", "coordinates": [4.9, 52.3]},
            }
        ],
    }


def detail_payload(address_id: UUID = ADDRESS_ID) -> dict[str, object]:
    return {
        "type": "Feature",
        "id": str(address_id),
        "properties": {
            "identificatie": "0000200000000001",
            "adresseerbaar_object_identificatie": "0000010000000001",
            "adresseerbaar_object_type": "Verblijfsobject",
            "openbare_ruimte_naam": "Examplelaan",
            "huisnummer": "10",
            "huisletter": None,
            "toevoeging": "A",
            "postcode": "1234AB",
            "woonplaats_naam": "Teststad",
        },
        "geometry": {"type": "Point", "coordinates": [4.9, 52.3]},
    }


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.anyio
async def test_location_search_maps_only_woonlens_contract_fields() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/search")
        assert request.url.params["q"] == "Examplelaan 10"
        assert request.url.params["adres[version]"] == "1"
        assert request.url.params["limit"] == "8"
        return httpx.Response(200, json=search_payload())

    async with client_for(handler) as client:
        adapter = PdokLocationSearchAdapter(client, "https://provider.test/v1/")
        result = await adapter.suggest("Examplelaan 10", limit=8)

    assert len(result) == 1
    assert result[0].id == ADDRESS_ID
    assert result[0].display_name == "Examplelaan 10, 1234AB Teststad"
    assert result[0].coordinates.longitude == 4.9
    assert result[0].coordinates.crs.endswith("CRS84")
    assert result[0].source.retrieved_at == RETRIEVED_AT
    assert result[0].source.license_name == "CC BY 4.0"


@pytest.mark.anyio
async def test_location_search_accepts_empty_results() -> None:
    payload = search_payload(count=0)
    payload["features"] = []

    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        result = await PdokLocationSearchAdapter(
            client, "https://provider.test/v1"
        ).suggest("Unknown", limit=8)

    assert result == ()


@pytest.mark.anyio
async def test_location_search_rejects_inconsistent_count() -> None:
    async with client_for(
        lambda _: httpx.Response(200, json=search_payload(count=2))
    ) as client:
        with pytest.raises(SourceContractError):
            await PdokLocationSearchAdapter(client, "https://provider.test/v1").suggest(
                "Example", limit=8
            )


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("status", "error"),
    [
        (404, AddressNotFoundError),
        (429, SourceRateLimitedError),
        (500, SourceUnavailableError),
        (400, SourceContractError),
    ],
)
async def test_provider_statuses_are_typed(status: int, error: type[Exception]) -> None:
    async with client_for(lambda _: httpx.Response(status)) as client:
        with pytest.raises(error):
            await PdokLocationSearchAdapter(client, "https://provider.test/v1").suggest(
                "Example", limit=8
            )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "handler",
    [
        lambda request: (_ for _ in ()).throw(
            httpx.ReadTimeout("slow", request=request)
        ),
        lambda request: (_ for _ in ()).throw(
            httpx.ConnectError("down", request=request)
        ),
    ],
)
async def test_network_failures_are_unavailable(
    handler: Callable[[httpx.Request], httpx.Response],
) -> None:
    async with client_for(handler) as client:
        with pytest.raises(SourceUnavailableError):
            await PdokLocationSearchAdapter(client, "https://provider.test/v1").suggest(
                "Example", limit=8
            )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, json={"type": "FeatureCollection"}),
    ],
)
async def test_invalid_search_payload_is_contract_error(
    response: httpx.Response,
) -> None:
    async with client_for(lambda _: response) as client:
        with pytest.raises(SourceContractError):
            await PdokLocationSearchAdapter(client, "https://provider.test/v1").suggest(
                "Example", limit=8
            )


@pytest.mark.anyio
@pytest.mark.parametrize("invalid_field", ["timestamp", "coordinates"])
async def test_invalid_search_spatial_metadata_is_contract_error(
    invalid_field: str,
) -> None:
    payload = search_payload()
    if invalid_field == "timestamp":
        payload["timeStamp"] = "2026-08-30T12:00:00"
    else:
        features = payload["features"]
        assert isinstance(features, list)
        feature = features[0]
        assert isinstance(feature, dict)
        feature["geometry"] = {"type": "Point", "coordinates": [200.0, 52.3]}

    async with client_for(lambda _: httpx.Response(200, json=payload)) as client:
        with pytest.raises(SourceContractError):
            await PdokLocationSearchAdapter(client, "https://provider.test/v1").suggest(
                "Example", limit=8
            )


@pytest.mark.anyio
async def test_bag_detail_maps_official_identifiers_and_uses_known_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "provider.test"
        assert request.url.path.endswith(f"/collections/adres/items/{ADDRESS_ID}")
        assert request.url.params["f"] == "json"
        return httpx.Response(200, json=detail_payload())

    async with client_for(handler) as client:
        adapter = PdokBagAddressAdapter(
            client,
            "https://provider.test/bag/",
            clock=lambda: RETRIEVED_AT,
        )
        result = await adapter.resolve(ADDRESS_ID)

    assert result.id == ADDRESS_ID
    assert result.number_designation_id == "0000200000000001"
    assert result.addressable_object_id == "0000010000000001"
    assert result.house_number_suffix == "A"
    assert result.source.retrieved_at == RETRIEVED_AT
    assert result.source.license_name == "Public Domain Mark 1.0"


@pytest.mark.anyio
async def test_bag_detail_rejects_different_returned_id() -> None:
    async with client_for(
        lambda _: httpx.Response(200, json=detail_payload(OTHER_ID))
    ) as client:
        with pytest.raises(SourceContractError):
            await PdokBagAddressAdapter(client, "https://provider.test/bag").resolve(
                ADDRESS_ID
            )
