# WoonLens

> Local-first Dutch housing comparison and data audit tool built on official public data.

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
- Preserve source timestamps, provenance, missing values, and data status
- Track changes between reproducible property snapshots
- Export a source-backed evidence report as JSON and PDF
- Run locally with the user's own API credentials

## Product principles

1. **Official sources first** — every fact must point back to its dataset.
2. **No invented certainty** — missing or conflicting data remains visible.
3. **Explain differences** — not every unequal value is a data error.
4. **Local-first privacy** — no user account or address-search logging is
   required for the self-hosted application.
5. **Reproducible output** — reports include query time, source, version, and
   transformation details.

## Initial data sources

| Source | Planned use |
| --- | --- |
| [PDOK Locatieserver](https://www.pdok.nl/restful-api/-/article/pdok-locatieserver-1) | Address resolution, BAG identifiers, and coordinates |
| [Kadaster BAG](https://api.pdok.nl/kadaster/bag/ogc/v2/api?f=html) | Building and residential-unit records |
| [EP-Online](https://public.ep-online.nl/swagger/index.html) | Registered energy-performance data |
| [CBS Open Data](https://www.cbs.nl/en-gb/our-services/open-data) | Neighbourhood and housing statistics |
| [RIVM Luchtmeetnet](https://data.rivm.nl/data/luchtmeetnet/) | Environmental measurements and context |

## Architecture direction

```text
Address input
    -> address resolution
    -> source-specific API clients
    -> normalized property snapshot
    -> validation and conflict rules
    -> comparison and change history
    -> JSON/PDF evidence report
```

The proposed implementation uses Python and FastAPI for the backend, PostgreSQL
with PostGIS for geospatial storage, and TypeScript with Next.js for the web
interface. These choices remain subject to validation during the first vertical
slice.

## Scope boundaries

WoonLens will not provide personal data, scrape property advertisements,
predict sale prices, offer mortgage advice, or present its output as legal,
valuation, or building-inspection advice.

## Development status

The project is currently in the repository-foundation phase. No production API
or user interface has been released yet. Work is tracked through GitHub Issues
and delivered with one branch and pull request per task.

The detailed MVP boundaries, delivery phases, quality requirements, and GitHub
work structure are defined in the [project scope](docs/PROJECT_SCOPE.md).

The [data journey](docs/DATA_JOURNEY.md) explains how an address moves through
PDOK, BAG, EP-Online, CBS, and Luchtmeetnet, including joins, uncertainty, and
remaining research questions. Endpoint-level requests and field mappings are
documented in the [data source API guide](docs/DATA_SOURCE_API.md).

Engineering conventions and recorded implementation decisions are maintained
in the [Software Engineering Handbook](docs/SOFTWARE_ENGINEERING.md).
The complete document set is listed in the
[documentation index](docs/README.md).

## Security and credentials

Copy `.env.example` to `.env` and add personal credentials only to the local
file. Never commit API keys, tokens, downloaded bulk datasets, or signed URLs.
Each user must obtain and configure their own EP-Online API key.

## Licensing

The WoonLens source code is licensed under the [MIT License](LICENSE). That
license applies to the code written for this repository, not to third-party
datasets. Dataset attribution and redistribution conditions will be documented
separately before data ingestion is released.

## Roadmap

1. Complete repository documentation, security, and licensing foundations.
2. Build a tested command-line vertical slice for one Dutch address.
3. Normalize and compare snapshots from the first official data sources.
4. Implement explainable cross-register validation rules.
5. Generate reproducible JSON and PDF evidence reports.
6. Add the local web interface, maps, automated tests, and release workflow.

Contributions will be welcome once the initial architecture and contribution
guidelines are merged.
