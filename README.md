# WoonLens

> Privacy-first Dutch housing comparison tool built on live official public data.

[![Status](https://img.shields.io/badge/status-foundation-informational)](#development-status)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Why WoonLens?

Important facts about Dutch homes are spread across multiple official systems.
A listing can show a floor area, an energy label, and a construction year, but
it rarely explains which register supplied each value, when it was updated, or
why two official sources disagree.

WoonLens is designed to compare homes and audit their public records. It will
not hide uncertainty behind a universal score or an opaque AI-generated
recommendation.

## Planned capabilities

- Compare two or more Dutch residential addresses side by side
- Resolve addresses and official identifiers through PDOK and BAG
- Retrieve registered energy-performance data from EP-Online
- Add neighbourhood context from CBS and environmental context from RIVM
- Detect field-level differences and possible conflicts between registers
- Explain different measurement scopes, such as registered BAG area versus
  EP-Online thermal-zone area
- Preserve source timestamps, provenance, missing values, and data status in
  each live comparison response
- Export the current source-backed comparison as JSON and PDF without retaining
  it on the server
- Work without an account, with optional accounts for saved searches,
  favourites, and comparison lists
- Re-fetch official data whenever a saved comparison is opened

## Product principles

1. **Official sources first** — every fact must point back to its dataset.
2. **No invented certainty** — missing or conflicting data remains visible.
3. **Explain differences** — not every unequal value is a data error.
4. **Data minimisation** — provider responses and derived property facts are
   processed in memory and are not persisted by WoonLens.
5. **Optional identity** — comparison works without an account; accounts store
   only user-owned search organisation data, never provider facts.

## Initial data sources

| Source | Planned use |
| --- | --- |
| [PDOK Location API](https://www.pdok.nl/location-api1) | Address search and links to official BAG address records |
| [Kadaster BAG](https://api.pdok.nl/kadaster/bag/ogc/v2/api?f=html) | Building and residential-unit records |
| [EP-Online](https://public.ep-online.nl/swagger/index.html) | Registered energy-performance data |
| [CBS Open Data](https://www.cbs.nl/en-gb/our-services/open-data) | Neighbourhood and housing statistics |
| [RIVM Luchtmeetnet](https://data.rivm.nl/data/luchtmeetnet/) | Environmental measurements and context |

## Architecture direction

```text
Address input
    -> address resolution
    -> source-specific API clients
    -> transient normalized property view
    -> validation and conflict rules
    -> live comparison
    -> optional JSON/PDF download
```

The proposed implementation uses Python and FastAPI for the backend, PostgreSQL
for optional accounts and saved-search references, and TypeScript with Next.js
for the web interface. Provider payloads and derived property facts are not
stored in PostgreSQL. These choices remain subject to validation during the
first vertical slice.

## Scope boundaries

WoonLens will not provide personal data, scrape property advertisements,
predict sale prices, offer mortgage advice, or present its output as legal,
valuation, or building-inspection advice.

## Development status

The backend foundation and guest live-comparison use case are implemented with
Python 3.13, FastAPI, `uv`, and Docker. A Next.js and TypeScript frontend
foundation provides the responsive application shell, design tokens, transient
query defaults, and browser-test harness. Guests can search official addresses
and build an in-memory selection of two to five homes, then request a live,
source-attributed comparison across property, energy, neighbourhood, and nearby
monitoring-station context. The active guest comparison can be regenerated as a
source-attributed JSON or PDF evidence download. Versioned backend rules also
surface neutral factual differences and cross-source checks without producing a
score or recommendation. Guests can inspect request-scoped BAG, EP-Online, CBS,
and monitoring-station detail panels from the same comparison snapshot; opening
a panel does not trigger another provider request. An optional, lazy-loaded map
shows numbered homes and relevant stations while preserving a complete textual
alternative. Official provider responses and generated files remain transient,
and no comparison database is used.

### Run locally

Docker is the canonical runtime:

```bash
docker compose up --build api frontend
curl http://localhost:8000/api/v1/health
```

Open `http://localhost:3000` for the web application. Compose also starts the
application PostgreSQL database, an ephemeral Redis session store, and a local
Keycloak development realm at `http://localhost:8080`. The **Sign in** action
uses the synthetic user `woonlens-demo` with password
`local-development-only`. These credentials and the Compose secrets are local
fixtures and must never be reused in production.

The expected API response is `{"status":"ok"}`. Run every implemented Python
quality gate in the same container environment:

```bash
docker compose --profile tools run --build --rm check
```

The first live-data vertical slice exposes transient official-address search
and resolution:

```http
GET /api/v1/addresses/suggest?q=Witte%20de%20Withstraat%2042A%20Rotterdam
GET /api/v1/addresses/resolve?id=690240c0-fc13-59d9-8e98-2ef441237a54
GET /api/v1/addresses/690240c0-fc13-59d9-8e98-2ef441237a54/administrative-context
GET /api/v1/addresses/690240c0-fc13-59d9-8e98-2ef441237a54/neighborhood-indicators
GET /api/v1/addresses/690240c0-fc13-59d9-8e98-2ef441237a54/property
GET /api/v1/addresses/690240c0-fc13-59d9-8e98-2ef441237a54/energy-registration
GET /api/v1/addresses/690240c0-fc13-59d9-8e98-2ef441237a54/overview
POST /api/v1/comparisons/live
POST /api/v1/comparison-downloads/json
POST /api/v1/comparison-downloads/pdf
PUT  /api/v1/account
GET  /api/v1/account
GET  /api/v1/account/export
DELETE /api/v1/account
GET  /api/v1/favourites
POST /api/v1/favourites
DELETE /api/v1/favourites/{id}
GET  /api/v1/favourites/{id}/address
GET  /api/v1/saved-comparisons
POST /api/v1/saved-comparisons
PATCH /api/v1/saved-comparisons/{id}
DELETE /api/v1/saved-comparisons/{id}
POST /api/v1/saved-comparisons/{id}/run
```

The account endpoints require the configured `woonlens:account` bearer scope.
Browser clients reach them through the Next.js BFF: Authorization Code and PKCE
run server-side, Redis stores AES-256-GCM-encrypted short-lived token state, and
the browser receives only an opaque `HttpOnly` cookie. The initial migration
stores only an internal account UUID, OIDC issuer, opaque subject, and creation
timestamp. Favourite storage adds only an owner-scoped record UUID, an opaque
PDOK address UUID, and its creation timestamp. Reopening a favourite resolves
the current address through PDOK; display labels and official property facts
remain request-scoped and are never written to the account database.
Guest endpoints remain anonymous and unchanged.

Saved comparisons retain only a user-supplied name and two to five ordered,
opaque PDOK address UUIDs. Opening a list resolves current address labels;
running it invokes the same live comparison pipeline as the guest journey.
Signed-in users can download a versioned JSON export containing only their
WoonLens account metadata, favourite address references, and ordered saved
comparison recipes. Account deletion removes those records together in one
database transaction, ends the local browser session, and does not delete or
modify the user's external OIDC identity. Neither lifecycle operation changes
the anonymous guest journey.

WoonLens uses the current PDOK Location API for search and the PDOK BAG OGC API
for the selected address detail. Requests and responses are not persisted or
cached, and address query strings are excluded from application access logs.
The administrative-context endpoint resolves the trusted BAG address again,
then joins its coordinates to current CBS neighbourhood, district,
municipality, and province boundaries through configured PDOK APIs. These
responses are also request-scoped and are never persisted.
The neighbourhood-indicators endpoint continues that trusted join into CBS
StatLine and returns a deliberately small housing-and-energy set. Every value
is labelled as neighbourhood-level context and carries its dataset year;
missing or suppressed observations remain missing rather than becoming zero.
The property endpoint resolves the address again, fetches its live BAG
residential-unit record, and returns every bounded related building with its
construction year and status. Registered BAG area is explicitly labelled and
is never presented as measured living area.
The energy-registration endpoint uses the trusted BAG residential-unit ID to
retrieve the latest non-expired EP-Online registration. It requires a personal
server-side EP-Online API key and keeps the credential and provider response
out of logs and storage.
The overview endpoint resolves the address once, starts independent BAG,
EP-Online, administrative-context, and Luchtmeetnet/RIVM requests concurrently,
and then retrieves neighbourhood indicators from the trusted context. Air
quality selects the nearest active compatible monitoring station independently
for NO2, PM10, and PM2.5 and labels every reading as station-level context.
Expected optional-source
failures produce explicit `unavailable_sections`; they do not erase successful
sections.
The live comparison endpoint accepts two to five unique address UUIDs and
returns ordered home overviews plus a stable metric table. Numeric deltas use
the first available value for the same metric as baseline; categorical and
definition-incompatible values are not forced into misleading arithmetic.
The same response includes versioned `insights` and per-home cross-source
`audits`. These rules describe extremes, ties, insufficient data, definition
differences, matches, and possible conflicts without declaring an overall
winner or inventing an energy-class score.

The JSON comparison-download endpoint reruns that live pipeline and returns a
downloadable evidence report. It adds a report schema version, UTC generation
time, source provenance, warnings, and limitations while retaining the full
comparison and its rule version. The response is marked `no-store`; WoonLens
does not write the report or its provider-derived facts to a database or file.
The PDF endpoint uses the same evidence contract to produce a readable,
multi-page A4 document with ordered homes, comparison tables, interpretations,
audits, unavailable-data warnings, sources, limitations, and page numbers.

The project is currently in the Guest Live Comparison foundation phase. The
backend runtime and its first official-data integrations are implemented; the
user interface has not been released yet. Work is tracked through GitHub
Issues and delivered with one branch and pull request per task.

The detailed MVP boundaries, delivery phases, quality requirements, and GitHub
work structure are defined in the [project scope](docs/PROJECT_SCOPE.md).
The [product feature map](docs/PRODUCT_FEATURE_MAP.md) connects guest and
account journeys to screens, backend use cases, and delivery phases.

The [data journey](docs/DATA_JOURNEY.md) explains how an address moves through
PDOK, BAG, EP-Online, CBS, and Luchtmeetnet, including joins, uncertainty, and
remaining research questions. Endpoint-level requests and field mappings are
documented in the [data source API guide](docs/DATA_SOURCE_API.md).

Engineering conventions and recorded implementation decisions are maintained
in the [Software Engineering Handbook](docs/SOFTWARE_ENGINEERING.md).
The complete document set is listed in the
[documentation index](docs/README.md).

## Security and credentials

Copy `.env.example` to `.env` for local overrides. The current foundation needs
no provider credentials. Never commit API keys, tokens, downloaded bulk
datasets, or signed URLs; credential setup will be documented with the first
integration that requires it.

## Licensing

The WoonLens source code is licensed under the [MIT License](LICENSE). That
license applies to the code written for this repository, not to third-party
datasets. Dataset attribution and redistribution conditions will be documented
separately before data ingestion is released.

## Roadmap

1. Complete the Docker-first backend and quality-gate foundation.
2. Build a tested address-resolution vertical slice for one Dutch address.
3. Normalize and compare live responses from the first official data sources.
4. Implement explainable cross-register validation rules.
5. Generate source-attributed JSON and PDF downloads without server retention.
6. Add the local web interface, maps, automated tests, and release workflow.

Contributions will be welcome once the initial architecture and contribution
guidelines are merged.
