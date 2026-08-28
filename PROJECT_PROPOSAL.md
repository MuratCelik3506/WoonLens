# WoonLens NL

> Official Dutch housing data, brought together.

WoonLens NL is an open-source web application that turns any Dutch residential
address into a transparent housing report. It helps renters, homebuyers,
residents, and expats understand a property using official public data rather
than advertisements, scraping, or opaque AI-generated scores.

## The Problem

Useful information about Dutch homes exists across several government systems,
but it is fragmented and difficult for ordinary users to compare. Property
listings rarely provide the full context around a building, its energy
performance, its neighbourhood, or its environment.

## The Product

A user enters one or two addresses. WoonLens NL resolves each address to its
official BAG records and produces a source-backed report containing:

- Building year, residential area, usage type, and official identifiers
- Registered energy label and registration details
- Neighbourhood housing, energy, and WOZ statistics
- Local air-quality indicators such as PM2.5, PM10, and NO2
- Comparisons with nearby and similar homes
- The source and freshness of every result

The main user promise is simple:

> Enter an address and see what the property listing does not tell you.

## Official Data Sources

| Source | Purpose |
| --- | --- |
| [PDOK Locatieserver](https://www.pdok.nl/restful-api/-/article/pdok-locatieserver-1) | Address search, BAG IDs, and coordinates |
| [Kadaster BAG](https://api.pdok.nl/kadaster/bag/ogc/v2/api?f=html) | Official building and residential-unit data |
| [EP-Online](https://public.ep-online.nl/swagger/index.html) | Registered energy labels |
| [CBS Neighbourhood Statistics](https://www.cbs.nl/nl-nl/cijfers/detail/86165NED) | Housing, energy, WOZ, and neighbourhood indicators |
| [RIVM Luchtmeetnet](https://data.rivm.nl/data/luchtmeetnet/) | Air-quality measurements |

## Data Flow

```text
Address
  -> PDOK address resolution
  -> BAG property records
  -> EP-Online energy label
  -> CBS neighbourhood spatial join
  -> RIVM air-quality spatial join
  -> validated report and comparison
```

## MVP

- Dutch address autocomplete
- Property report based on official records
- Energy-label lookup
- Neighbourhood and air-quality context
- Side-by-side comparison of two addresses
- Source and last-updated information
- Shareable report URL
- Public JSON API
- English user interface
- Docker-based local setup and automated tests

The MVP will not include property advertisements, personal data, price
predictions, mortgage advice, or an unexplained universal housing score.

## Proposed Architecture

- **Backend:** Python, FastAPI, PostgreSQL, PostGIS
- **Frontend:** Next.js, TypeScript, MapLibre
- **Data:** Incremental ingestion jobs, raw snapshots, validation, provenance
- **Operations:** Docker Compose, GitHub Actions, structured logs, health checks

Every derived value must remain traceable to its original dataset. Missing data
will be shown honestly rather than predicted.

## Initial Roadmap

1. Build a command-line vertical slice for one real Dutch address.
2. Design the PostGIS schema and reproducible ingestion pipeline.
3. Implement the public property-report and comparison API.
4. Build the searchable web report and interactive map.
5. Add automated synchronization, monitoring, tests, and documentation.
6. Publish a hosted demo and the first open-source release.

## Success Criteria

- One address produces a report from at least four official sources.
- Two addresses can be compared in a single view.
- Property-level and neighbourhood-level facts are clearly separated.
- Every result includes its source and data timestamp.
- The complete application runs locally from documented commands.
- Core ingestion, comparison, and geospatial logic is automatically tested.

## Repository

Detailed source requests, verified responses, and field mappings are documented
in [`docs/DATA_SOURCE_API.md`](docs/DATA_SOURCE_API.md).

**Suggested name:** `woonlens-nl`

**GitHub description:**

> Open-source housing intelligence for the Netherlands. Explore buildings,
> energy labels, neighbourhood statistics, and environmental data by address.
