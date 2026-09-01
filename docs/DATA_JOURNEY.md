# The WoonLens Data Journey

## Purpose of This Document

This document tells the story of how one address becomes a source-backed,
transient WoonLens property view. It explains what each external API knows, what
WoonLens asks for, what comes back, how the sources connect, and where the
application must remain cautious.

It complements the endpoint-level examples in
[`DATA_SOURCE_API.md`](DATA_SOURCE_API.md). That guide is the request and field
reference; this document is the conceptual integration narrative.

## Verification Snapshot

The source chain was last rechecked on **2026-08-30** with the following public
address:

```text
Witte de Withstraat 42A, 3012BR Rotterdam
```

The verification checked live service availability and response shape. It did
not save credentials, authenticated headers, signed URLs, or full production
responses.

| Source | Live result | What was verified |
| --- | --- | --- |
| PDOK Location API | `200 OK` | Address search, UUID, display value, and CRS84 point |
| PDOK BAG address detail | `200 OK` | Number designation and addressable-object identifiers |
| Kadaster BAG OGC API | `200 OK` | Residential-unit schema and building relation |
| EP-Online Public REST API v5 | `200 OK` | Authenticated array response and BAG join fields |
| CBS StatLine OData v4 | `200 OK` | Dataset entities, measure metadata, and units |
| Luchtmeetnet Open API | `200 OK` | Station schema, measurement schema, and pagination |

Official references:

- [PDOK Location API](https://www.pdok.nl/location-api1)
- [Kadaster BAG OGC API](https://api.pdok.nl/kadaster/bag/ogc/v2?f=html&lang=en)
- [EP-Online Public REST API v5](https://public.ep-online.nl/swagger/index.html)
- [CBS OData v4 metadata guide](https://www.cbs.nl/nl-nl/onze-diensten/open-data/statline-als-open-data/metadata-odata-v4)
- [Luchtmeetnet Open API](https://api-docs.luchtmeetnet.nl/)

Live verification proves that the documented path works at one point in time.
It is not a guarantee that an upstream schema, dataset, rate limit, or service
term will never change.

## The Story in One Diagram

```text
What the user types
        |
        v
PDOK Location search ---- user confirms the intended address
        |
        v
PDOK BAG address detail
        |
        +---- BAG addressable-object ID -------------------+
        |                                                  |
        +---- BAG address ID                               |
        |                                                  v
        +---- coordinates                                  |
        |                                                  |
        v                                                  |
Kadaster BAG residential unit ---- building relation -----+
        |                                                  |
        v                                                  |
Official property facts                                   |
                                                           |
coordinates ---------> CBS spatial join -> neighbourhood  |
                                      -> StatLine statistics|
                                                           |
coordinates ---------> compatible monitoring station      |
                              |                            |
                              v                            |
                    Luchtmeetnet observations              |
                                                           |
        +--------------------------------------------------+
        v
Transient normalized view -> validation rules -> live comparison -> optional download
```

The addressable-object ID is the strongest cross-source property join in the
initial chain. Coordinates lead to contextual spatial joins; those results are
not additional facts about the individual home.

## Chapter 1 — A Person Types an Address

The journey begins with an imprecise human input:

```text
Witte de Withstraat 42 Rotterdam
```

This is not yet a safe database key. It might refer to `42`, `42A`, another
suffix, or an address written with a different spelling. WoonLens therefore
does not parse the text and guess.

Instead, it calls the current PDOK Location API search endpoint and restricts
the search to address collection version 1:

```http
GET https://api.pdok.nl/kadaster/location-api/v1/search
    ?q=Witte%20de%20Withstraat%2042%20Rotterdam
    &adres[version]=1
    &limit=5
    &f=json
```

### What WoonLens asks for

- The user's partial address text in `q`, between 2 and 200 characters
- Only address collection version 1 with `adres[version]=1`
- A small result set suitable for an autocomplete list

### What comes back

The search response contains lightweight GeoJSON features. A result includes:

- `id`: the UUID of the linked BAG OGC address feature
- `properties.display_name`: the human-readable address
- `properties.collection_id` and `collection_version`
- `geometry`: a CRS84 point
- `properties.score`: search relevance, which WoonLens does not expose as a
  quality or property score

The live check returned four matching suggestions for the example query. This
is why WoonLens must show the options and let the user choose. A relevance
score is not permission to silently replace `42` with `42A`.

### The first important rule

The result UUID is used only for the next live detail request. WoonLens does not
persist it as a property record, does not expose the provider's detail URL, and
does not silently select a top-ranked result.

## Chapter 2 — The Selection Receives Official Identifiers

After the user selects a suggestion, WoonLens validates the UUID and constructs
a request against the fixed PDOK BAG address collection:

```http
GET https://api.pdok.nl/kadaster/bag/ogc/v2/collections/adres/items/
    690240c0-fc13-59d9-8e98-2ef441237a54?f=json
```

The BAG address response turns the selected result into the initial integration
passport:

| Meaning | Source field | Verified example |
| --- | --- | --- |
| BAG address | `identificatie` | `0599200000508415` |
| BAG addressable object | `adresseerbaar_object_identificatie` | `0599010000295420` |
| Address type | `adresseerbaar_object_type` | `Verblijfsobject` |
| Location | `geometry.coordinates` | CRS84 longitude/latitude |

These values open different doors:

- `adresseerbaarobject_id` connects the address to the BAG residential unit
  and EP-Online registrations.
- `identificatie` preserves the official number-designation identity.
- Coordinates support map display and later spatial context such as
  neighbourhood and monitoring-station selection.

All official identifiers are treated as strings in the transient model. Leading
zeroes are part of the identity and must never be lost through integer
conversion. District and neighbourhood codes are no longer claimed to come
from address resolution; they require a later spatial/contextual join.

## Chapter 3 — BAG Describes the Registered Physical Object

With the 16-digit addressable-object ID, WoonLens asks the Kadaster BAG OGC API
for the `verblijfsobject` record:

```http
GET https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject/items
    ?f=json
    &identificatie=0599010000295420
    &limit=1
```

The BAG API is open, requires no authentication, is provided without a usage
fee, and identifies its data as Public Domain Mark 1.0. The official service
metadata reports daily updates.

### What the residential-unit record knows

The live schema includes:

- Official object identity
- Object status
- Usage purposes
- Registered area
- Address fields
- Source-document metadata
- Administrative place names and identifiers
- One or more `pand.href` building relations

The residential unit and the building are not the same object. An apartment is
a residential unit inside a building; one residential unit can also relate to
more than one building. WoonLens must follow every returned building relation
instead of assuming a single building.

### Following the building relation

The `pand.href` value points to a BAG building feature. WoonLens validates its
origin and exact collection path, extracts the feature UUID, and reconstructs
the request from the configured BAG base URL. It never follows an arbitrary
provider-returned URL. The resulting building record returns facts such as:

- BAG building ID
- Construction year
- Building status
- Usage purposes
- Number of related residential units where available

The OGC feature URL or feature UUID is not necessarily the official BAG
building identification. WoonLens stores them separately and treats the
returned `identificatie` as the official building ID.

This chapter is implemented by
`GET /api/v1/addresses/{address_id}/property`. The response exists only for the
request, includes source and licence metadata, and preserves missing provider
fields as `null` instead of inventing values.

### What BAG does not tell us

BAG's registered area is not an energy calculation area, a measured interior
area, or a guarantee of current physical condition. BAG also does not tell us
the current energy label. Those facts belong to other sources and definitions.

## Chapter 4 — EP-Online Adds the Energy Registration

The same BAG addressable-object ID is sent to EP-Online:

```http
GET https://public.ep-online.nl/api/v5/PandEnergielabel/
    AdresseerbaarObject/0599010000295420
Authorization: <personal API key>
```

The actual request URL is a single line; it is wrapped above for readability.

### Access requirements

EP-Online differs from the other initial APIs:

- A personal API key is required.
- The key is sent in the `Authorization` header.
- Every self-hosted user must obtain their own key.
- The key is stored only in a local `.env` file.
- It must never appear in commits, logs, fixtures, reports, screenshots, or
  GitHub Issues.

The live authenticated request returned `200 OK`. The response was an array
containing one registration. Even a single result is represented as an array,
so the adapter must support zero, one, or multiple registrations.

### What an energy registration contains

The verified v5 schema includes:

- Registration, inspection, and validity dates
- Registration status and calculation method
- Building class, type, and subtype
- BAG residential-unit and building IDs
- Construction year
- Thermal-zone area
- Energy class
- Energy demand
- Primary fossil energy
- Renewable-energy share
- Calculated CO2 emissions and energy use
- Additional nullable energy-performance indicators

### How EP-Online connects back to BAG

EP-Online returns both `BAGVerblijfsobjectID` and `BAGPandIDs`. WoonLens must
verify that the returned residential-unit ID equals the non-placeholder ID it
requested. The returned building IDs can then be cross-checked against BAG.

This gives WoonLens two useful comparisons:

1. BAG construction year versus EP-Online construction year
2. BAG registered area versus EP-Online thermal-zone area

Neither difference is automatically an error. The area values describe
different scopes. WoonLens retains both, attaches their definitions, and lets a
validation rule explain the difference.

### Selecting a current registration

All returned registrations must remain available in memory while the current
label is selected. A tentative display rule is:

1. Reject records whose BAG object ID does not match the request.
2. Exclude expired registrations for the current-label view.
3. Select the matching record with the latest registration date.

This rule is implemented by
`GET /api/v1/addresses/{address_id}/energy-registration`. Multiple,
expired-only, empty, mismatched-identity, missing-credential, and provider-error
responses are covered by deterministic tests. Provider responses and normalized
registrations are discarded after the request completes.

### Bulk and mutation files are out of scope

EP-Online also exposes metadata for total and daily mutation files. The live
comparison does not call these endpoints or follow their signed download URLs.
Bulk ingestion and provider-history storage are outside the product scope.

## Chapter 5 — The Address Enters Its Neighbourhood

The administrative-context use case resolves the selected BAG address again so
that the backend, rather than the client, supplies the trusted CRS84 point. It
queries current CBS boundaries through PDOK and returns official codes and
names for the containing neighbourhood, district, municipality, and province.

```http
GET https://api.pdok.nl/cbs/wijken-en-buurten-2026/ogc/v1/
    collections/buurten/items
    ?f=json
    &bbox=<small non-zero box around the BAG point>
    &limit=2
```

The actual request URL is a single line; it is wrapped above for readability.

The neighbourhood result supplies neighbourhood, district, and municipality
codes and names. A concurrent, year-filtered CBS Gebiedsindelingen request
supplies the province. No boundary geometry or upstream response is persisted.
No match and ambiguous matches are explicit outcomes; missing levels are not
invented.

### The level-of-detail boundary

This data describes the neighbourhood, not the selected home. A neighbourhood
average must never be displayed as a property fact.

For example:

```text
Correct:   Average residential WOZ value in this neighbourhood: EUR 372,000
Incorrect: This property's WOZ value: EUR 372,000
```

The geometry dataset helps WoonLens identify and display the area. More
specific housing and energy indicators come from CBS StatLine.

## Chapter 6 — CBS Numbers Need Their Dictionary

CBS StatLine OData v4 is not a simple object containing descriptive field
names. It is cell-oriented: observations refer to measure identifiers, and
metadata tables explain what those identifiers mean.

For dataset `85984NED`, the service advertises these relevant entities:

- `MeasureGroups`
- `MeasureCodes`
- `Dimensions`
- `WijkenEnBuurtenGroups`
- `WijkenEnBuurtenCodes`
- `Observations`
- `Properties`

### First request: learn the measure definitions

WoonLens fetches `MeasureCodes` and stores the identifier, title, and unit. The
live check confirmed these initial measures:

| Measure ID | Official meaning | Official unit |
| --- | --- | --- |
| `M001642` | Average residential WOZ value | EUR × 1,000 |
| `M000221_2` | Average electricity delivery | kWh |
| `M008294` | Average electricity returned | kWh |
| `M000219_2` | Average natural-gas consumption | m³ |
| `M008297` | Homes with solar power | % |

The frontend must not hardcode these labels and units without retaining the
source metadata. A measure definition may be corrected or redesigned upstream.

### Second request: fetch observations

WoonLens filters `Observations` by both neighbourhood code and selected measure
IDs. It then joins:

```text
Observations.Measure = MeasureCodes.Identifier
```

An observation only becomes meaningful when combined with:

- Measure definition and unit
- Neighbourhood code
- Dataset identifier and year
- `ValueAttribute`, including special or missing-value meaning
- Retrieval timestamp

### Why the newest table is not always the answer

During the initial investigation, the 2025 table contained the selected WOZ
observation for the example neighbourhood but not all selected household energy
measures. The 2024 table contained the complete initial set.

WoonLens therefore selects the latest complete year per metric rather than
assuming that the newest dataset is complete for every measure. The report
must disclose the year attached to each metric. It must not silently combine
different years under one generic “current” label.

The first implemented slice intentionally pins all five selected measures to
dataset `85984NED` (2024). It does not yet implement per-metric year selection.
The public endpoint accepts only the address UUID, obtains the current official
neighbourhood internally, and returns the 2024 dataset identity beside every
result set. Boundary changes can therefore produce explicit missing values.

CBS OData responses can be paginated. This implementation requests only five
known measures with server-side filters. A next link in that bounded response
is treated as a contract error; the adapter does not follow an arbitrary URL.

## Chapter 7 — Air Quality Comes From a Station, Not the Front Door

The address coordinates can support a search for nearby Luchtmeetnet stations.
The API has separate station and measurement resources.

For the station used in the verified integration path:

```http
GET https://api.luchtmeetnet.nl/open_api/stations/NL01487
```

Station metadata includes:

- Station location and geometry
- Station type, such as traffic
- Operator organisation
- Municipality and province
- Supported measurement components
- Start year

Measurements are requested separately:

```http
GET https://api.luchtmeetnet.nl/open_api/stations/NL01487/measurements
    ?formula=NO2
    &order=timestamp_measured
    &order_direction=desc
    &page=1
```

The live response contained a `data` collection and pagination metadata. Each
measurement contains:

- `formula`
- `value`
- `timestamp_measured`
- `timestamp_measured_start`
- `timestamp_measured_end`

### The spatial honesty rule

A station reading is not a measurement at the selected address. The report
must show:

- Station name and identifier
- Operator
- Station type
- Straight-line distance from the address
- Pollutant
- Measurement window
- Whether the value is provisional or ratified when known

The implemented selection downloads the current official RIVM location,
measurement-series, and component catalogues during the request. It excludes
ended records and selects the nearest active compatible station independently
for NO2, PM10, and PM2.5 using great-circle distance. Different pollutants may
use different stations. Distance alone does not make a traffic station
representative of residential background exposure, so station type and distance
remain visible and the values are never ranked.

The measurement response does not itself provide a unit. WoonLens joins the
pollutant to current official component metadata and rejects incomplete unit
metadata. The RIVM catalogue code `PM2.5` maps explicitly to live API formula
`PM25`.

Long historical ingestion is outside the stateless product scope. Only live
measurements needed for the current comparison are requested.

### From a live comparison to a JSON evidence report

`POST /api/v1/comparison-downloads/json` starts with the same two-to-five
official address UUIDs and reruns the live comparison pipeline. The application
then wraps that request-scoped result with report schema version `1.0.0`, a UTC
generation time, a deduplicated source index, comparison warnings, and explicit
limitations. The existing ordered homes, metrics, rule version, insights, and
audits remain intact.

Each successful fact continues to carry provider, dataset, retrieval time, and
license metadata. Missing optional sections keep their safe reason codes. The
report never contains provider credentials, headers, signed URLs, raw response
bodies, or exception details.

The API serializes the report directly into an attachment response marked
`Cache-Control: no-store`. It creates no server-side report file and performs no
database write. Once the HTTP request finishes, the application retains no copy
of the generated report or its provider-derived contents.

The PDF route follows this identical application journey. Only the final
presentation adapter changes: it lays out the normalized evidence as a
landscape A4 document with repeating table headers, source attribution,
limitations, and page numbers. PDF bytes are returned directly in the HTTP
response and are not saved on the server.

## Chapter 8 — The Sources Meet in a Transient Normalized View

The source adapters do not merge raw JSON objects directly. Each adapter maps
its response into a typed fragment while retaining provenance.

Raw payloads and normalized values exist only within request-scoped processing.
They are not written to application storage, logs, server-side report files,
or caches. A user-requested download serializes only the normalized evidence
contract directly into the current response.

Guest and signed-in users use this same live pipeline. A signed-in user may save
a favourite or named comparison reference, but reopening it starts the source
journey again; the earlier provider facts are not restored from WoonLens.

The implemented composition endpoint is:

```http
GET /api/v1/addresses/{address_id}/overview
```

It resolves the official address once. BAG property, EP-Online energy, and
administrative-context requests then start concurrently. Neighbourhood
indicators follow only after a trusted neighbourhood code is available. Address
resolution is the required root; expected downstream source failures are
reported per section so unrelated successful sections remain usable.

A simplified result looks like this:

```json
{
  "address": {
    "bag_address_id": "0599200000508415",
    "bag_object_id": "0599010000295420",
    "neighbourhood_code": "BU05990112"
  },
  "property": {
    "registered_area_m2": 62,
    "construction_year": 1873
  },
  "energy": {
    "energy_class": "B",
    "thermal_zone_area_m2": 54.41
  },
  "neighbourhood": {
    "dataset_year": 2024,
    "average_woz_eur": 372000
  },
  "unavailable_sections": [
    {
      "section": "energy_registration",
      "reason": "source_configuration_error"
    }
  ]
}
```

The values above are included to explain the verified example shape. They are
not application fixtures and must be retrieved again for every comparison.
Each populated section carries its own source metadata in the actual API
response. Failure entries contain only stable reason codes and never provider
payloads, credentials, or exception text.

### From one overview to a live comparison

The core guest comparison endpoint is:

```http
POST /api/v1/comparisons/live
```

It accepts two to five unique official address UUIDs, preserves their order,
and starts their overview journeys concurrently. One unavailable address does
not erase other homes. The response contains eight deliberately stable metrics:
BAG registered area, unambiguous construction year, energy class, EP-Online
thermal-zone area, energy demand, primary fossil energy, renewable-energy
share, and CBS neighbourhood average WOZ.

For each numeric metric, the first available selected home is the baseline and
later values receive a same-definition delta. Energy class remains categorical.
BAG registered area is never subtracted from EP-Online thermal-zone area, and
neighbourhood WOZ is explicitly local context rather than a valuation of the
selected property.

### Versioned interpretation, not automated judgement

Comparison rule set `1.0.0` adds two derived collections to the transient
response:

- `insights` describes ties, data gaps, descriptive extremes, directional
  energy indicators, and values that must not be ranked;
- `audits` evaluates fields from two sources for the same home.

No overall winner is produced. Larger registered area and newer construction
year are preference or descriptive facts. Lower reported energy demand and
primary fossil energy are directional indicators, not bills or guarantees.
Energy classes remain official categories rather than being converted to an
invented score.

The area audit always classifies two available area values as
`definition-difference`, because BAG registered area and EP-Online thermal-zone
area describe different scopes. The construction-year audit returns `match`,
`missing`, or `possible-conflict`; a possible conflict asks for source review
instead of asserting that one register is wrong.

### Provenance travels with every value

Every normalized value must retain:

- Provider and dataset
- Endpoint, collection, table, and measure ID where applicable
- Original object ID and source field
- Dataset or reference period
- Retrieval timestamp
- Source status
- Transformation rule and version
- Applicable attribution

This is what lets WoonLens answer not only “what is the value?” but also “who
said it, when, at what geographic level, and according to which definition?”

## Chapter 9 — Differences Become Explanations

Once the transient view exists, explicit rules evaluate relationships without erasing
the original values.

### Example: two area values

```text
BAG registered area:             62 m²
EP-Online thermal-zone area:     54.41 m²
```

The correct result is not automatically “8 m² data error.” The sources describe
different measurement scopes. WoonLens should label the difference, link both
definitions, and only raise a potential conflict if a tested rule justifies it.

### Example: construction year

If BAG and EP-Online return the same year, WoonLens can mark the values as
cross-source consistent. If they differ, both values remain visible with their
source dates and statuses. The system does not silently choose a winner.

### Example: missing CBS metric

An absent observation is represented as a typed missing value. It is never
converted to zero and is never filled from another year without disclosing the
fallback.

## Chapter 10 — Failure Is Part of the Data Story

Each adapter must distinguish transport, authentication, validation, and data
availability failures.

| Situation | Meaning inside WoonLens |
| --- | --- |
| Timeout or upstream `5xx` | Source temporarily unavailable; retry safely |
| `401` from EP-Online | Missing or inactive personal credential |
| Invalid identifier | Reject locally before calling the provider |
| Valid identifier with `404` | Typed source-specific not-found result |
| Empty CBS observation | Missing metric, not zero |
| Paginated response | Incomplete until every required page is read |
| Unknown field or schema change | Contract failure; do not guess a mapping |
| Partial source failure | Preserve successful sources and disclose the failure |

Retries must use timeouts, backoff, and a small attempt limit. User-input errors
and authentication failures are not retryable. Optional contextual sources
should not erase successfully retrieved official property facts.

## Chapter 11 — Recommended Adapter Boundaries

The implementation should keep one client per upstream responsibility:

```text
PdokLocationSearchClient
    suggest_address(query)

PdokBagAddressClient
    resolve_address(address_uuid)

BagClient
    get_residential_unit(bag_object_id)
    get_building(feature_url)

EpOnlineClient
    get_energy_registrations(bag_object_id)

CbsGeometryClient
    get_neighbourhood(neighbourhood_code, dataset_year)

CbsStatLineClient
    get_measure_codes(dataset_id, measure_ids)
    get_observations(dataset_id, area_code, measure_ids)

LuchtmeetnetClient
    load_active_locations_series_and_components()
    select_nearest_compatible_station(address_coordinates, pollutant)
    get_latest_measurements(selected_station_ids)
```

An orchestration service owns the journey. Individual clients must not know
about frontend presentation or silently join unrelated sources.

## Chapter 12 — What Is Known and What Still Needs Proof

### Confirmed enough for the first vertical slice

- Current PDOK Location API address search and BAG address-detail contracts
- BAG residential-unit retrieval by official object ID
- Following BAG building relations
- EP-Online authentication and addressable-object query
- EP-Online BAG join fields
- CBS OData service structure and selected 2024 measure metadata
- Luchtmeetnet station and measurement response shapes
- Nearest active compatible station selection for NO2, PM10, and PM2.5
- Official pollutant labels and units from RIVM component metadata
- The cross-source identifier chain for the verified address

### Must be resolved during implementation

- Final EP-Online current-registration selection using multiple-record fixtures
- Rate-limit and retry policies for every provider
- Upstream schema-contract monitoring
- CBS dataset discovery and per-measure year-selection automation
- CBS special-value and `ValueAttribute` mapping catalogue
- Rules for station representativeness, not only distance
- Promotion from `current-unratified` to ratified status when the live source
  publishes a trustworthy status field
- Account-data minimisation and deletion rules for saved search references
- Re-verification of third-party terms before public release

These are implementation tasks, not details to hide behind defaults.

## Chapter 13 — Definition of Done for a Source Adapter

A source adapter is complete only when:

1. Its official documentation and applicable terms are linked.
2. Authentication and secret handling are documented.
3. Request parameters and identifiers are validated locally.
4. Success, empty, not-found, invalid, unauthorized, timeout, and upstream
   failure behaviours are defined.
5. Raw and normalized response models are separate.
6. Every normalized field has a source-field mapping and unit policy.
7. Missing values remain distinguishable from zero.
8. Pagination is implemented where required.
9. Deterministic redacted or synthetic fixtures cover the contract.
10. Optional live smoke tests are disabled by default.
11. Provenance and attribution are retained.
12. Schema changes fail visibly instead of producing guessed values.

## Closing Perspective

WoonLens is not valuable merely because it calls several APIs. Its value comes
from respecting what each source can legitimately claim.

PDOK tells us which official object the user selected. BAG describes the
registered residential unit and building. EP-Online describes an energy
registration linked through BAG. CBS places the address inside a statistical
area. Luchtmeetnet describes observations at a monitoring station. WoonLens
preserves those boundaries, records the evidence, and explains the differences
without inventing certainty.
