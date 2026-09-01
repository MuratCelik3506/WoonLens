# WoonLens — Data Source API Guide

This document defines the first verified integration path from one Dutch
address to a transient normalized WoonLens property view. The comparison layer runs
this source chain independently for each selected address and compares the
normalized views in memory; it does not compare unrelated raw API fields directly.

The examples below use one real address throughout the complete chain.

## Verification Status

**Test date:** 2026-08-30
**Test address:** Witte de Withstraat 42A, 3012BR Rotterdam

| Step | Source | Result |
| --- | --- | --- |
| 1 | PDOK Location API + BAG address detail | `200 OK` — address UUID, BAG identifiers, and CRS84 coordinates returned |
| 2 | Kadaster BAG OGC API | `200 OK` — residential unit and building returned |
| 3 | EP-Online v5 | `200 OK` — authenticated label and file metadata returned |
| 4 | CBS/PDOK neighbourhood geometry | `200 OK` — neighbourhood returned |
| 5 | CBS StatLine OData | `200 OK` — housing and energy observations returned |
| 6 | Luchtmeetnet Open API | `200 OK` — station metadata and hourly NO2 returned |

No response examples in this document are invented. Signed download URLs and
the project API key are intentionally excluded.

Third-party licensing, attribution, and redistribution boundaries are tracked
separately in [`DATA_LICENSING.md`](DATA_LICENSING.md).

## Integration Contract

The source chain is:

```text
search text
  -> PDOK Location API address UUID + coordinates
  -> PDOK BAG address detail
  -> BAG addressable-object ID
  -> BAG residential unit and building
  -> EP-Online energy-label registrations
  -> CBS neighbourhood geometry and statistics
  -> Luchtmeetnet station metadata and measurements
  -> transient normalized WoonLens property view
```

For a multi-address comparison, WoonLens repeats this chain for every address,
holds each normalized view and its retrieval context only for the request, and
then evaluates explicit comparison and explanation rules.

For every source, WoonLens must:

1. validate and transform the response in memory without writing the provider
   payload to application storage, logs, reports, or caches;
2. validate required identifiers and value types;
3. normalize only documented fields;
4. retain source name, source URL, fetch time, and dataset year;
5. represent unavailable values as `null`, never as zero;
6. avoid deriving claims that the source does not support;
7. preserve source definitions, reference dates, and provisional/ratified
   status where available.

Provider responses, normalized facts, and comparison results are request-scoped
and must not be written to the application database, filesystem, logs, report
store, analytics, or application cache. Optional accounts may retain only the
minimum user-owned search or comparison reference needed to run these requests
again.

---

## 1. PDOK Location API and BAG Address Detail

**Purpose:** address autocomplete and conversion of a user-selected address to
official BAG identifiers and coordinates.

- [Official product documentation](https://www.pdok.nl/location-api1)
- [Location API OpenAPI](https://api.pdok.nl/kadaster/location-api/v1/api?f=html)
- [BAG OGC API OpenAPI](https://api.pdok.nl/kadaster/bag/ogc/v2/api?f=html)
- Authentication: none
- Location API license: CC BY 4.0
- BAG license: Public Domain Mark 1.0

### 1.1 Suggest an Address

```bash
curl -sS --get \
  'https://api.pdok.nl/kadaster/location-api/v1/search' \
  --data-urlencode 'q=Witte de Withstraat 42A Rotterdam' \
  --data-urlencode 'adres[version]=1' \
  --data-urlencode 'limit=5' \
  --data-urlencode 'f=json'
```

Verified first result:

```json
{
  "id": "690240c0-fc13-59d9-8e98-2ef441237a54",
  "properties": {
    "collection_id": "adres",
    "collection_version": 1,
    "display_name": "Witte de Withstraat 42A, 3012BR Rotterdam, Rotterdam (Zuid-Holland)"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [4.477563182494074, 51.91559870274542]
  }
}
```

The search is restricted to `adres` collection version 1. The result UUID is a
PDOK BAG OGC feature identifier; it is used transiently to request the selected
address detail. It is not persisted as a WoonLens property record.

### 1.2 Resolve the Selected Address

```bash
curl -sS \
  'https://api.pdok.nl/kadaster/bag/ogc/v2/collections/adres/items/690240c0-fc13-59d9-8e98-2ef441237a54?f=json'
```

Verified identifiers:

```json
{
  "id": "690240c0-fc13-59d9-8e98-2ef441237a54",
  "properties": {
    "identificatie": "0599200000508415",
    "adresseerbaar_object_identificatie": "0599010000295420",
    "adresseerbaar_object_type": "Verblijfsobject",
    "openbare_ruimte_naam": "Witte de Withstraat",
    "huisnummer": "42",
    "huisletter": "A",
    "toevoeging": null,
    "postcode": "3012BR",
    "woonplaats_naam": "Rotterdam"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [4.477563182494074, 51.91559870274542]
  }
}
```

### Field Processing

| Source field | Internal field | Handling |
| --- | --- | --- |
| Search `id` | `id` | UUID used only to resolve the selected address |
| Search `display_name` | `display_name` | Display value; never parse identifiers from it |
| Search `geometry.coordinates` | `coordinates` | Longitude then latitude with explicit CRS84 |
| BAG `identificatie` | `number_designation_id` | Zero-preserving official BAG address identifier |
| BAG `adresseerbaar_object_identificatie` | `addressable_object_id` | Zero-preserving downstream property join key |
| BAG `adresseerbaar_object_type` | `addressable_object_type` | Retain provider meaning |
| BAG `openbare_ruimte_naam` | `street` | Unicode string |
| BAG `huisnummer` | `house_number` | Retain as returned string |
| BAG `huisletter` | `house_letter` | Nullable string |
| BAG `toevoeging` | `house_number_suffix` | Nullable string |
| BAG `postcode` | `postal_code` | Retain official compact form |
| BAG `woonplaats_naam` | `city` | Unicode string |

### Validation

- Require collection `adres`, collection version 1, feature type `Feature`, and
  point geometry from the search contract.
- Require a valid UUID and exact UUID equality in the resolved BAG feature.
- Construct the BAG detail request from the configured HTTPS base URL and UUID;
  never follow an arbitrary URL from a client or payload.
- Keep leading zeroes in every BAG code.
- Return all bounded suggestions for user confirmation; do not silently select
  or replace an address variant.
- Treat missing required fields, wrong collection versions, invalid geometry,
  or inconsistent result counts as provider-contract errors.

---

## 2. Kadaster BAG OGC API

**Purpose:** official residential-unit and building facts.

- [Official OpenAPI specification](https://api.pdok.nl/kadaster/bag/ogc/v2/api?f=html)
- Authentication: none
- Format used: GeoJSON

### 2.1 Fetch the Residential Unit

Implemented endpoint:

```http
GET /api/v1/addresses/{address_id}/property
```

`address_id` is the UUID returned by address search. WoonLens resolves it again
and derives the 16-digit BAG addressable-object ID internally; clients cannot
submit an arbitrary upstream BAG query through this endpoint.

```bash
curl -sS --get \
  'https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject/items' \
  --data-urlencode 'f=json' \
  --data-urlencode 'identificatie=0599010000295420' \
  --data-urlencode 'limit=10'
```

Verified result:

```json
{
  "identificatie": "0599010000295420",
  "status": "Verblijfsobject in gebruik",
  "gebruiksdoel": "onderwijsfunctie,woonfunctie",
  "oppervlakte": 62,
  "postcode": "3012BR",
  "huisnummer": 42,
  "huisletter": "A",
  "pand.href": [
    "https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items/1a55ae8d-1fa9-5cc4-85e7-fda7f1e626d2"
  ]
}
```

### 2.2 Follow the Building Relation

The `pand.href` value is an OGC feature URL, not the building's BAG
identification. WoonLens does not follow this provider-controlled URL directly.
It verifies the configured origin and exact collection path, extracts only the
feature UUID, and constructs a new request against the fixed configured BAG
endpoint:

```bash
curl -sS --get \
  'https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items/1a55ae8d-1fa9-5cc4-85e7-fda7f1e626d2' \
  --data-urlencode 'f=json'
```

Verified building facts:

```json
{
  "identificatie": "0599100000691863",
  "bouwjaar": 1873,
  "status": "Pand in gebruik",
  "aantal_verblijfsobjecten": 4,
  "gebruiksdoel": "onderwijsfunctie,winkelfunctie,woonfunctie"
}
```

### Residential-Unit Field Processing

| Source field | Internal field | Handling |
| --- | --- | --- |
| feature `id` | `bag_feature_id` | OGC feature identifier, separate from BAG ID |
| `identificatie` | `bag_object_id` | Canonical join key |
| `status` | `unit_status` | Preserve original Dutch value and optionally map to an enum |
| `gebruiksdoel` | `usage_purposes` | Split comma-separated value into a deduplicated list |
| `oppervlakte` | `registered_area_m2` | Integer; registered BAG area, not measured living area |
| `geconstateerd` | `was_formally_observed` | Map `J/N` to boolean only after validation |
| `documentdatum` | `source_document_date` | ISO date |
| `documentnummer` | `source_document_number` | Provenance field |
| `hoofdadres_identificatie` | `main_bag_address_id` | String join key |
| address fields | normalized address fields | Cross-check against PDOK; BAG wins on conflict |
| `pand.href` | related building UUIDs | Validate origin/path, extract UUID, and query a fixed endpoint; one unit can reference multiple buildings |
| feature geometry | `unit_location` | Point in EPSG:4326 |
| `rdf_seealso` | `source_uri` | Provenance link |

### Building Field Processing

| Source field | Internal field | Handling |
| --- | --- | --- |
| feature `id` | `bag_building_feature_id` | OGC feature identifier |
| `identificatie` | `bag_building_id` | Canonical building identifier |
| `bouwjaar` | `construction_year` | Integer; validate a plausible range |
| `status` | `building_status` | Preserve original value |
| `gebruiksdoel` | `building_usage_purposes` | Normalize to a list |
| `aantal_verblijfsobjecten` | `residential_unit_count` | Integer |
| `geconstateerd` | `was_formally_observed` | Validated `J/N` mapping |
| `documentdatum` | `source_document_date` | ISO date |
| `documentnummer` | `source_document_number` | Provenance field |
| `verblijfsobject.href` | `unit_feature_urls` | Relationship list |
| feature geometry | `building_footprint` | Polygon/MultiPolygon in EPSG:4326 |

Do not label every BAG `oppervlakte` value as “living area.” A mixed-use unit
can have multiple usage purposes, as the verified example demonstrates.
The live implementation bounds the number of related buildings with
`WOONLENS_BAG_MAX_RELATED_BUILDINGS` (default `10`) before making building
requests. Provider results are request-scoped and are not persisted or cached.

---

## 3. EP-Online Public REST API v5

**Purpose:** official energy-label registrations.

- [Official Swagger UI](https://public.ep-online.nl/swagger/index.html)
- Authentication: API key in the `Authorization` header
- Join key: 16-digit BAG addressable-object ID

### Local Credential Setup

Implemented endpoint:

```http
GET /api/v1/addresses/{address_id}/energy-registration
```

The public endpoint accepts only the address UUID produced by official address
search. WoonLens resolves that UUID again and derives the BAG residential-unit
ID internally before contacting EP-Online.

The repository contains a committed `.env.example` and a Git-ignored `.env`.
Add the personal production key only to `.env`:

```dotenv
WOONLENS_EP_ONLINE_API_KEY=your-personal-key
```

`.env.example` contains only an empty variable as a safe configuration hint.
Never add a populated key to `.env.example`, source code, test fixtures,
screenshots, issues, or documentation. Self-hosted users must obtain and
configure their own key.

### Request

```bash
curl -sS \
  -H "Authorization: ${WOONLENS_EP_ONLINE_API_KEY}" \
  'https://public.ep-online.nl/api/v5/PandEnergielabel/AdresseerbaarObject/0599010000295420'
```

Verified authenticated response summary:

```json
[
  {
    "Registratiedatum": "2026-02-04T15:31:59.943",
    "Opnamedatum": "2026-01-14T00:00:00",
    "Geldig_tot": "2036-01-14T00:00:00",
    "Soort_opname": "Basisopname",
    "Status": "Bestaand",
    "Gebouwklasse": "Woningbouw",
    "Gebouwtype": "Appartement",
    "Gebouwsubtype": "Tussenmidden",
    "BAGVerblijfsobjectID": "0599010000295420",
    "BAGPandIDs": ["0599100000691863"],
    "Bouwjaar": 1873,
    "Gebruiksoppervlakte_thermische_zone": 54.41,
    "Energieklasse": "B",
    "Energiebehoefte": 109.02,
    "PrimaireFossieleEnergie": 172.52,
    "Aandeel_hernieuwbare_energie": 0.0,
    "BerekendeCO2Emissie": 31.80,
    "BerekendeEnergieverbruik": 172.51
  }
]
```

The equivalent address query also returned `200 OK` and the same single
registration:

```bash
curl -sS --get \
  -H "Authorization: ${WOONLENS_EP_ONLINE_API_KEY}" \
  'https://public.ep-online.nl/api/v5/PandEnergielabel/Adres' \
  --data-urlencode 'postcode=3012BR' \
  --data-urlencode 'huisnummer=42' \
  --data-urlencode 'huisletter=A'
```

The initial request without a key returned:

```json
{
  "status": 401,
  "title": "Unauthorized",
  "detail": "Valid API key required to access this resource."
}
```

The successful response is always modeled as an array of
`PandEnergielabelV5` objects, including when only one registration exists.

### File Metadata Endpoints — Research Only

EP-Online exposes total and mutation-file metadata, but WoonLens does not use
bulk ingestion in the stateless live-comparison product. The endpoints below
remain documented only as verified provider behaviour and must not be called by
the address-comparison workflow.

Latest monthly total-file metadata:

```bash
curl -sS --get \
  -H "Authorization: ${WOONLENS_EP_ONLINE_API_KEY}" \
  'https://public.ep-online.nl/api/v5/Mutatiebestand/DownloadInfo' \
  --data-urlencode 'fileType=csv'
```

Verified safe fields:

```json
{
  "bestandsnaam": "v20260801_v4_csv.zip",
  "geldigTotEnMet": "2026-08-29T21:05:55.3783303+02:00"
}
```

Daily mutation-file metadata:

```bash
curl -sS --get \
  -H "Authorization: ${WOONLENS_EP_ONLINE_API_KEY}" \
  'https://public.ep-online.nl/api/v5/Mutatiebestand/DownloadInfo/2026-08-27'
```

Verified safe fields:

```json
{
  "bestandsnaam": "d20260827_v4.zip",
  "geldigTotEnMet": "2026-08-29T21:06:25.6717026+02:00"
}
```

Both responses also contain a temporary signed `downloadUrl`. WoonLens must not
request, store, log, publish, cache, or follow that URL. Valid provider file
types are `xml`, `csv`, and `xlsx`, but bulk-file processing is out of scope.

### Verified Error Behaviour

| Scenario | Verified status | Adapter behaviour |
| --- | ---: | --- |
| Missing or inactive API key | `401` | Configuration/authentication error |
| Invalid BAG ID format | `400` | Reject before calling the provider |
| Valid-format unknown BAG ID | `404` | Return `energy_label: null` with a typed not-found reason |
| Invalid address parameters | `400` | Reject before calling the provider |
| Invalid mutation date format | `400` | Reject before calling the provider |
| Removed daily mutation file | `404` | Research-only endpoint; no application action |

`0000000000000000` is a dangerous legacy placeholder, not a safe unknown ID.
The live API returned many unrelated historical registrations for it. WoonLens
must reject this value locally and must verify that every returned
`BAGVerblijfsobjectID` equals the requested non-placeholder BAG ID.

### Implemented response selection

WoonLens validates every returned `BAGVerblijfsobjectID`, removes registrations
whose `Geldig_tot` date has passed, and selects the remaining record with the
latest `Registratiedatum`. An empty response or a response containing only
expired registrations becomes a typed not-found result. The complete upstream
array is discarded when the request ends.

### Complete v5 Field Processing Plan

| Source field | Internal field or action |
| --- | --- |
| `Registratiedatum` | `registration_date` |
| `Opnamedatum` | `inspection_date` |
| `Geldig_tot` | `valid_until` |
| `Certificaathouder` | `certificate_holder` |
| `Soort_opname` | `assessment_type` |
| `Status` | `registration_status` |
| `Berekeningstype` | `calculation_method` |
| `IsVereenvoudigdLabel` | `is_simplified_label` |
| `Op_basis_van_referentiegebouw` | `uses_reference_building` |
| `Gebouwklasse` | `building_class` |
| `Gebouwtype` | `building_type` |
| `Gebouwsubtype` | `building_subtype` |
| `SBIcode` | `sbi_code` |
| `Postcode` | Cross-check only; BAG remains canonical |
| `Huisnummer` | Cross-check only |
| `Huisletter` | Cross-check only |
| `Huisnummertoevoeging` | Cross-check only |
| `Detailaanduiding` | `building_detail` |
| `BAGVerblijfsobjectID` | `bag_object_id` |
| `BAGLigplaatsID` | `bag_berth_id` |
| `BAGStandplaatsID` | `bag_pitch_id` |
| `BAGPandIDs` | `bag_building_ids` |
| `Bouwjaar` | Cross-check with BAG; retain both values on conflict |
| `Gebruiksoppervlakte_thermische_zone` | `thermal_zone_area_m2` |
| `Compactheid` | `compactness` |
| `Energieklasse` | `energy_class` |
| `EnergieIndex` | `energy_index` |
| `EnergieIndex_EMG_forfaitair` | `energy_index_emg_default` |
| `Energiebehoefte` | `energy_demand_kwh_m2_year` |
| `PrimaireFossieleEnergie` | `primary_fossil_energy_kwh_m2_year` |
| `Primaire_fossiele_energie_EMG_forfaitair` | `primary_fossil_energy_emg_default_kwh_m2_year` |
| `Aandeel_hernieuwbare_energie` | `renewable_energy_share_pct` |
| `Aandeel_hernieuwbare_energie_EMG_forfaitair` | `renewable_energy_share_emg_default_pct` |
| `Temperatuuroverschrijding` | `summer_overheating_indicator` |
| `Warmtebehoefte` | `heating_demand_kwh_m2_year` |
| `Eis_energiebehoefte` | `required_max_energy_demand_kwh_m2_year` |
| `Eis_primaire_fossiele_energie` | `required_max_primary_fossil_energy_kwh_m2_year` |
| `Eis_aandeel_hernieuwbare_energie` | `required_min_renewable_energy_share_pct` |
| `Eis_temperatuuroverschrijding` | `required_max_overheating_indicator` |
| `BerekendeCO2Emissie` | `calculated_co2_kg_m2_year` |
| `BerekendeEnergieverbruik` | `calculated_energy_use_kwh_m2_year` |

All nullable fields must remain nullable. All returned registrations must remain
available during selection in the current request. For the displayed current label, first exclude expired registrations
and records whose BAG ID does not match the request, then select the greatest
`Registratiedatum`. Multiple-registration fixtures still need verification
before this rule is treated as final.

---

## 4. CBS Administrative Context via PDOK

**Purpose:** identify the current official neighbourhood, district,
municipality, and province containing a resolved BAG address coordinate.

- [CBS Wijken en Buurten 2026 OGC API](https://api.pdok.nl/cbs/wijken-en-buurten-2026/ogc/v1?f=html&lang=en)
- [CBS Gebiedsindelingen OGC API](https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1?f=html&lang=en)
- Authentication: none
- License: CC BY 4.0
- Update frequency: annual; the configured dataset year must match the
  published boundary edition
- Spatial input: the CRS84 point obtained from the fixed BAG address-detail
  endpoint, never a client-supplied name or area code

### Request

```bash
curl -sS --get \
  'https://api.pdok.nl/cbs/wijken-en-buurten-2026/ogc/v1/collections/buurten/items' \
  --data-urlencode 'f=json' \
  --data-urlencode 'bbox=4.89999,52.36999,4.90001,52.37001' \
  --data-urlencode 'limit=2'

curl -sS --get \
  'https://api.pdok.nl/cbs/gebiedsindelingen/ogc/v1/collections/provincie_gegeneraliseerd/items' \
  --data-urlencode 'f=json' \
  --data-urlencode 'bbox=4.89999,52.36999,4.90001,52.37001' \
  --data-urlencode 'jaarcode=2026' \
  --data-urlencode 'limit=2'
```

Verified result summary:

```json
{
  "neighborhood": {"code": "BU0363AF08", "name": "Zuiderkerkbuurt"},
  "district": {"code": "WK0363AF", "name": "Nieuwmarkt/Lastage"},
  "municipality": {"code": "GM0363", "name": "Amsterdam"},
  "province": {"code": "PV27", "name": "Noord-Holland"}
}
```

OGC API Features rejects a zero-area point `bbox`, so WoonLens sends a tiny
non-zero bounding box around the trusted address point and requests at most two
features. Zero matches produce a typed no-coverage result. One match is mapped;
more than one is rejected as ambiguous rather than guessed. The two independent
source requests run concurrently. Partial coverage remains explicit: an area is
`null` and only the sources that contributed values are returned.

### Field Policy

| Field group | Handling |
| --- | --- |
| Official codes and names | Include in the transient response |
| Dataset year and retrieval time | Preserve as provenance |
| Boundary geometry | Use only for the provider spatial query; do not expose or store |
| Statistical indicators | Out of scope for this context endpoint |
| Unknown provider fields | Ignore; required contract fields still validate strictly |

The PDOK neighbourhood geometry is not the source for the complete WOZ and
energy set. Those values come from CBS StatLine OData.

---

## 5. CBS StatLine OData

**Purpose:** neighbourhood-level housing and energy indicators.

- [CBS OData documentation](https://www.cbs.nl/nl-nl/onze-diensten/open-data/statline-als-open-data/metadata-odata-v4)
- [2024 dataset](https://www.cbs.nl/nl-nl/cijfers/detail/85984NED)
- Authentication: none
- Implemented endpoint:
  `GET /api/v1/addresses/{address_id}/neighborhood-indicators`

### Why the 2024 Table Is Used Initially

The 2025 table (`86165NED`) was tested first. For `BU05990112`, it returned the
WOZ observation but no electricity, gas, electricity-return, or solar
observations. The 2024 table (`85984NED`) returned all five selected metrics.

WoonLens must therefore choose the latest complete year per metric, not assume
that the newest dataset contains every measure.

### Metadata Request

CBS uses measure identifiers rather than descriptive property names. Fetch and
join `MeasureCodes` in memory before interpreting observations.

```bash
curl -sS --get \
  'https://datasets.cbs.nl/odata/v1/CBS/85984NED/MeasureCodes' \
  --data-urlencode \
  "\$filter=contains(Title,'WOZ') or contains(Title,'elektriciteit') or contains(Title,'aardgas') or contains(Title,'zonnestroom')" \
  --data-urlencode '$select=Identifier,Title,Unit'
```

### Observation Request

```bash
curl -sS --get \
  'https://datasets.cbs.nl/odata/v1/CBS/85984NED/Observations' \
  --data-urlencode \
  "\$filter=WijkenEnBuurten eq 'BU05990112' and (Measure eq 'M001642' or Measure eq 'M000221_2' or Measure eq 'M008294' or Measure eq 'M000219_2' or Measure eq 'M008297')" \
  --data-urlencode '$select=Measure,Value,ValueAttribute,WijkenEnBuurten'
```

Verified observations:

| Measure | Meaning | Unit | Verified value |
| --- | --- | --- | ---: |
| `M001642` | Average residential WOZ value | EUR × 1,000 | 372 |
| `M000221_2` | Average electricity delivery | kWh | 1,690 |
| `M008294` | Average electricity returned | kWh | 10 |
| `M000219_2` | Average natural-gas consumption | m³ | 140 |
| `M008297` | Homes with solar power | % | 1 |

These are neighbourhood statistics. The WOZ value must be presented as a
neighbourhood average of EUR 372,000, never as the selected property's value.

The implemented public response uses stable WoonLens keys while preserving the
CBS measure identifier, title, source unit, dataset identifier, dataset year,
retrieval time, and licence. `M001642` is multiplied by 1,000 and returned with
the explicit normalized unit `EUR`; the original `x 1 000 euro` unit remains in
`source_unit`.

The address UUID is resolved through BAG and the neighbourhood code is resolved
through the administrative-context adapter. A client cannot submit its own
neighbourhood code. The adapter validates that the code matches `BU` followed
by eight digits before constructing the OData filter.

### Observation Processing

- Join `Observations.Measure` to `MeasureCodes.Identifier`.
- Return the source unit instead of hardcoding a unit in the frontend.
- Require exactly one metadata definition for each selected measure.
- Reject duplicate or unexpected selected observations.
- An omitted observation becomes `value: null` with
  `missing_reason: not_published`.
- A null observation preserves its CBS `ValueAttribute` as the missing reason.
- A numeric observation with a non-neutral `ValueAttribute` is rejected rather
  than displayed ambiguously.
- Any `@odata.nextLink` in these tightly filtered five-row responses is rejected
  as an incompatible contract; arbitrary provider URLs are never followed.
- Neither metadata nor observations are cached or persisted.

The current administrative boundary year is 2026 while this complete metric
set is pinned to 2024. A neighbourhood code changed between those editions may
therefore have no observations. That temporal mismatch is returned as missing
data and must never be silently replaced with another area's figures.
- Interpret `Value` only together with `ValueAttribute`.
- If an observation is absent, keep it absent; do not fall back to zero.
- Include `dataset_id`, `dataset_year`, `measure_id`, and `fetched_at` with every
  normalized metric in the response.
- Follow `@odata.nextLink` whenever a query is paginated.

---

## 6. Luchtmeetnet Open API

**Purpose:** station metadata and recent hourly air-quality measurements.

- [Official API documentation](https://api-docs.luchtmeetnet.nl/)
- [Historical RIVM downloads](https://data.rivm.nl/data/luchtmeetnet/)
- Authentication: none
- Documented limit: 100 requests per five minutes
- Documented refresh: hourly

### 6.1 Fetch Station Metadata

```bash
curl -sS \
  'https://api.luchtmeetnet.nl/open_api/stations/NL01487'
```

Verified station:

```json
{
  "type": "Traffic",
  "components": ["PM25", "NO", "FN", "PM10", "BCWB", "NO2"],
  "geometry": {
    "type": "point",
    "coordinates": [4.48066, 51.89113]
  },
  "municipality": "Rotterdam",
  "organisation": "DCMR (Rijnmond)",
  "location": "Rotterdam-Pleinweg"
}
```

### 6.2 Fetch Hourly Measurements

```bash
curl -sS --get \
  'https://api.luchtmeetnet.nl/open_api/stations/NL01487/measurements' \
  --data-urlencode 'formula=NO2' \
  --data-urlencode 'order=timestamp_measured' \
  --data-urlencode 'order_direction=desc' \
  --data-urlencode 'page=1'
```

Verified first observation at test time:

```json
{
  "value": 25.2,
  "formula": "NO2",
  "timestamp_measured": "2026-08-28T18:00:00+00:00",
  "timestamp_measured_start": "2026-08-28T17:00:00+00:00",
  "timestamp_measured_end": "2026-08-28T18:00:00+00:00"
}
```

### Field Processing

| Source field | Internal field | Handling |
| --- | --- | --- |
| station number | `station_id` | Stable provider identifier |
| `location` | `station_name` | Display with organisation |
| `organisation` | `station_operator` | Provenance |
| `type` | `station_type` | Important context, e.g. traffic station |
| `components` | `supported_components` | Use to prevent unsupported queries |
| station geometry | `station_location` | Point in EPSG:4326 |
| `formula` | `pollutant_code` | Preserve source code such as `NO2`, `PM10`, `PM25` |
| `value` | `measured_value` | Nullable numeric value |
| measurement timestamps | start/end/representative time | Parse as timezone-aware UTC timestamps |

The API measurement response does not include a unit. WoonLens retrieves the
official RIVM component metadata and requires the unit published for each
selected pollutant before showing a value.

Station observations are not address-level measurements. The report must show
the station name, station type, distance from the address, and observation time.
For every request, WoonLens retrieves the current RIVM measurement-location,
measurement-series, and component metadata. Ended locations and series are
excluded. For each of `NO2`, `PM10`, and `PM2.5`, it calculates CRS84 great-circle
distance and selects the nearest active station with a compatible air series.
Different pollutants may therefore select different stations. The RIVM
`PM2.5` catalogue code maps explicitly to the live API formula `PM25`.

Only page 1 of the selected station's measurements is requested, ordered by
measurement time. The newest non-null row for the required formula is retained.
No catalogue, response, selected station, or observation is persisted.

Long historical ingestion is outside the stateless product scope. WoonLens uses
only the live measurements required for the current comparison.

---

## Normalized Report Shape

The source adapters should eventually produce a response shaped like this:

```json
{
  "address": {
    "display_address": "Witte de Withstraat 42A, 3012BR Rotterdam",
    "bag_address_id": "0599200000508415",
    "bag_object_id": "0599010000295420",
    "location": {"longitude": 4.47756318, "latitude": 51.9155987}
  },
  "property": {
    "registered_area_m2": 62,
    "usage_purposes": ["onderwijsfunctie", "woonfunctie"],
    "buildings": [
      {
        "bag_building_id": "0599100000691863",
        "construction_year": 1873,
        "status": "Pand in gebruik"
      }
    ]
  },
  "energy_label": {
    "class": "B",
    "registered_at": "2026-02-04T15:31:59.943",
    "valid_until": "2036-01-14T00:00:00",
    "building_type": "Appartement",
    "thermal_zone_area_m2": 54.41,
    "energy_demand_kwh_m2_year": 109.02,
    "primary_fossil_energy_kwh_m2_year": 172.52,
    "renewable_energy_share_pct": 0.0
  },
  "neighbourhood": {
    "code": "BU05990112",
    "name": "Cool",
    "statistics_year": 2024,
    "average_woz_eur": 372000,
    "average_electricity_kwh": 1690,
    "average_gas_m3": 140,
    "homes_with_solar_pct": 1
  },
  "air_quality": {
    "observations": [
      {
        "pollutant": "NO2",
        "value": 14.35,
        "unit": "µg/m³",
        "scope": "monitoring-station",
        "status": "current-unratified",
        "station": {"id": "NL10418", "distance_km": 0.471}
      }
    ],
    "missing_pollutants": []
  },
  "sources": []
}
```

The energy-label object is backed by a verified authenticated response. The
air-quality example is station context and must not be presented as an
address-level measurement, exposure estimate, limit-value assessment, or
health conclusion.

## Live Home Overview Contract

The implemented orchestration endpoint is:

```http
GET /api/v1/addresses/{address_id}/overview
```

The resolved address is mandatory. The following sections are optional and
independently attributed:

| Section | Scope | Trusted dependency |
| --- | --- | --- |
| `property` | Residential unit and building | BAG object ID from resolved address |
| `energy_registration` | Residential unit | Same BAG object ID |
| `administrative_context` | Address coordinate | CRS84 coordinate from resolved address |
| `neighborhood_indicators` | Neighbourhood | CBS neighbourhood code from administrative context |
| `air_quality` | Monitoring station | CRS84 address coordinate plus active RIVM series metadata |

Independent downstream calls start concurrently. Expected typed source,
configuration, not-found, and unsupported-object failures set the relevant
section to `null` and add a stable entry to `unavailable_sections`. If
administrative context is unavailable, neighbourhood indicators receive
`dependency_unavailable`. Unexpected programming errors are not hidden as
partial success.

The overview does not introduce persistence or caching. A new request repeats
the live source journey.

## Stateless Multi-Home Comparison Contract

```http
POST /api/v1/comparisons/live
Content-Type: application/json

{
  "address_ids": [
    "690240c0-fc13-59d9-8e98-2ef441237a54",
    "11111111-1111-4111-8111-111111111111"
  ]
}
```

The request requires two to five unique UUIDs. Output order matches input order,
while overview work begins concurrently. Each metric returns:

- a stable key and human-readable label;
- the data scope and unit;
- a definition that prevents category mistakes;
- one value or explicit missing reason per requested home;
- a baseline marker; and
- a delta only when the metric supports same-definition numeric comparison.

The first available value for an individual numeric metric is its baseline.
This allows a later home to remain comparable when an earlier home or section
is unavailable. It does not make the first home intrinsically better.

The response includes an `area_definition_difference` notice because BAG
registered area and EP-Online thermal-zone area are separate metrics with
different meanings. It also includes a `neighborhood_context` notice so CBS
aggregates are not presented as facts about an individual property.
The `monitoring_station_context` notice states that recent air-quality readings
come from nearby stations and are not address measurements or health
conclusions. NO2, PM10, and PM2.5 comparison metrics do not calculate deltas.

The request, live provider fragments, normalized overviews, comparison table,
and deltas are discarded after the response.

### Interpretation rule set 1.1.0

The comparison response includes:

| Field | Meaning |
| --- | --- |
| `rules_version` | Version of the deterministic interpretation contract |
| `insights` | Cross-home descriptions tied to stable metric rule IDs |
| `audits` | Per-home cross-source checks tied to stable audit rule IDs |

Insight classifications are `same`, `insufficient_data`,
`descriptive_extreme`, `directional_indicator`, `context_only`, and
`not_ranked`. Address UUID arrays identify every tied home selected by a rule.
Rule set `1.1.0` adds `not_ranked` station-context interpretations for available
air-quality metrics and `insufficient_data` when no selected home has a recent
compatible observation. It never chooses a lower-reading home as a winner.

The initial cross-source audits are:

| Rule ID | Fields | Classifications |
| --- | --- | --- |
| `area.definition.v1` | BAG registered area, EP-Online thermal-zone area | `definition-difference`, `missing` |
| `construction_year.cross_source.v1` | BAG construction year, EP-Online construction year | `match`, `missing`, `possible-conflict` |

Interpretation messages use normalized values only. They contain no raw
provider response, exception text, signed URL, or credential. Updating a rule's
meaning requires a new rule ID or rules version.

## Transient JSON Evidence Report Contract

```http
POST /api/v1/comparison-downloads/json
Content-Type: application/json

{
  "address_ids": [
    "690240c0-fc13-59d9-8e98-2ef441237a54",
    "11111111-1111-4111-8111-111111111111"
  ]
}
```

This endpoint accepts the same two-to-five unique address UUID contract as the
live comparison. It runs the same source retrieval, normalization, comparison,
interpretation, and audit pipeline; it does not accept provider facts supplied
by a client.

The `1.0.0` report contract contains:

| Field | Meaning |
| --- | --- |
| `schema_version` | Version of the downloadable report structure |
| `generated_at` | Timezone-aware UTC report generation time |
| `rules_version` | Version of the interpretation rules used |
| `comparison` | Ordered homes, metrics, notices, insights, and audits |
| `sources` | Deduplicated provider, dataset, retrieval time, and license records |
| `warnings` | Human-readable comparison notices |
| `limitations` | Boundaries against valuation, inspection, and false certainty |

Successful output uses `application/json`, a safe
`woonlens-comparison-<UTC timestamp>.json` attachment filename, and
`Cache-Control: no-store`. Source metadata remains present both beside the
relevant home facts and in the report-level source index. Optional unavailable
sections and missing metric reasons remain explicit; no value is synthesized.

The generated document exists only as the current HTTP response. WoonLens does
not persist the request, provider payloads, normalized overviews, comparison,
report, or filename. Credentials, authorization headers, signed URLs, raw
provider bodies, and internal exception text are excluded from the contract.

### Transient PDF presentation

```http
POST /api/v1/comparison-downloads/pdf
Content-Type: application/json
```

The request body and live data journey are identical to the JSON evidence
report. A successful response uses `application/pdf`, a safe
`woonlens-comparison-<UTC timestamp>.pdf` attachment filename, and
`Cache-Control: no-store`.

The landscape A4 document presents:

- report and comparison-rule versions plus UTC generation time;
- compared addresses in request order;
- one value or explicit missing reason per metric and home;
- versioned interpretations and cross-source audits;
- unavailable-section warnings and comparison notices;
- provider, dataset, retrieval time, and license metadata;
- required limitations and a non-retention statement; and
- a footer and page number on every page.

Tables can continue across pages with repeated column headers. PDF generation
uses only the normalized evidence model; it does not embed raw provider payloads
or hidden attachments. The bytes are streamed in the response and are never
written to server-side storage.

## Comparison and Audit Contract

WoonLens compares transient normalized views, but it must not treat every unequal
number as an error. Each evaluated field difference should receive one of the
following classifications:

| Classification | Meaning |
| --- | --- |
| `match` | Comparable values agree within the documented tolerance |
| `definition-difference` | Values use different scopes or measurement definitions |
| `temporal-difference` | Values may differ because their reference dates differ |
| `missing` | A required source or value is unavailable |
| `possible-conflict` | Comparable values disagree and no known explanation rule applies |
| `not-comparable` | The fields must not be evaluated against each other |

For example, BAG `registered_area_m2` and EP-Online
`thermal_zone_area_m2` describe different concepts. Their numerical difference
may be useful evidence, but it is a `definition-difference`, not automatically
a register error.

Every audit result must retain:

- the two source fields and values being evaluated;
- their definitions and reference dates;
- the classification and rule identifier;
- a human-readable explanation;
- the rule/version and evaluation timestamp.

## Next Verification Steps

1. Perform an authenticated EP-Online smoke test when a personal key is
   configured locally; never capture the raw response or credential.
2. Download the complete Luchtmeetnet station catalogue and calculate the
   nearest station that supports each requested component.
3. Verify pollutant units from official metadata.
4. Turn every field rule in this document into adapter contract tests.
5. Continue using synthetic contract fixtures; runtime provider responses must
   not become fixtures.
