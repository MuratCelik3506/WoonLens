# WoonLens — Project Proposal

## One-line summary

WoonLens is a local-first, open-source tool for comparing Dutch homes,
auditing official property records, and generating reproducible evidence
reports.

## Problem

Dutch housing information is distributed across several official systems.
These systems use different identifiers, reference dates, geographic levels,
and measurement definitions. A homebuyer or renter can find individual facts,
but cannot easily answer:

- Which official source produced this value?
- When was it last updated?
- Why do two registers show different areas or construction details?
- Has the public record changed since an earlier inspection?
- Can the result be reproduced and shared without trusting an opaque score?

Existing address dashboards usually aggregate values into cards. They rarely
turn source differences, uncertainty, and provenance into a first-class product.

## Proposed solution

A user enters two or more Dutch residential addresses. WoonLens resolves their
official identifiers, requests data from selected public sources, normalizes
the responses, and creates comparable property snapshots.

The system then applies explicit validation rules. It distinguishes genuine
conflicts from values that differ because they describe different concepts. For
example, a BAG registered area and an EP-Online thermal-zone area may both be
correct while using different measurement scopes.

The result is a transparent due-diligence evidence pack containing:

- A side-by-side property comparison
- Source-level facts and missing-data indicators
- Explainable warnings and cross-register differences
- Retrieval dates and source provenance
- Historical snapshot changes
- Reproducible JSON and PDF reports

## Target users

- Renters and homebuyers comparing candidate homes
- Expats navigating unfamiliar Dutch public registers
- Residents checking the public facts associated with their address
- Researchers and civic-technology developers exploring housing data quality
- Inspectors or advisers who need a traceable preliminary evidence bundle

WoonLens is informational software. It is not a valuation, mortgage, legal, or
building-inspection service.

## Product differentiation

The project is not defined by calling several APIs. Its differentiating layer
is the evidence and reconciliation workflow:

1. Compare multiple homes instead of returning one isolated address card.
2. Preserve source definitions rather than flattening unlike values.
3. Detect and explain field-level differences between official registers.
4. Version property snapshots so later changes can be inspected.
5. Produce an export that records how and when every result was obtained.
6. Run locally with user-owned credentials and no mandatory account.

## Initial data sources

| Source | Purpose |
| --- | --- |
| PDOK Locatieserver | Address resolution, coordinates, and BAG identifiers |
| Kadaster BAG | Buildings, residential units, registered area, usage, and construction year |
| EP-Online | Registered energy-performance facts and thermal-zone measurements |
| CBS Open Data | Neighbourhood-level housing and demographic context |
| RIVM/Luchtmeetnet | Environmental measurements with provisional/ratified status |

Every integration remains isolated behind a source-specific client. Upstream
responses are mapped into a normalized model without discarding original
identifiers or provenance.

## MVP scope

### Included

- Address search and normalization
- Comparison of two to five addresses
- BAG and EP-Online property snapshots
- Selected CBS and RIVM context
- Field definitions and source timestamps
- Explainable cross-source validation rules
- Missing-data and stale-data indicators
- JSON evidence export
- Basic PDF evidence report
- Local Docker-based setup
- Automated unit, contract, and optional live integration tests

### Excluded

- Property advertisement scraping
- Personal owner or resident information
- Sale-price prediction
- Mortgage recommendations
- A universal or AI-generated property score
- Automatic legal or inspection conclusions
- Redistribution of restricted bulk source data

## User journey

```text
Select 2–5 addresses
    -> resolve official address and BAG identifiers
    -> retrieve source-specific records
    -> normalize property snapshots
    -> evaluate definitions, freshness, and conflicts
    -> compare homes side by side
    -> export a reproducible evidence report
```

## Architecture direction

- **Backend:** Python and FastAPI
- **Validation:** Pydantic models and explicit rule objects
- **Database:** PostgreSQL with PostGIS for snapshots and geospatial context
- **Frontend:** TypeScript, Next.js, and MapLibre
- **Jobs:** Idempotent source synchronization and snapshot creation
- **Testing:** Pytest, deterministic fixtures, contract tests, and limited live smoke tests
- **Operations:** Docker Compose, GitHub Actions, structured logs, and health checks

The first implementation milestone will be a command-line vertical slice. It
must resolve one real address and produce a normalized, source-backed JSON
snapshot before database or frontend complexity is introduced.

## Provenance model

Every normalized value should retain:

- Provider and dataset
- Endpoint, table, or collection identifier
- Original object and field identifier
- Reference period and data status
- Retrieval timestamp
- Transformation and validation rule
- Applicable attribution text

A generated report must disclose missing sources, failed requests, provisional
data, and rules that could not be evaluated.

## Open-source and data policy

WoonLens code is released under the MIT License. Third-party data remains under
its own terms and is not relicensed by this repository.

The repository will contain code, documentation, synthetic fixtures, and
minimal redacted examples. It will not contain personal API keys, address-search
logs, restricted bulk exports, or source datasets whose redistribution terms
have not been confirmed.

Each self-hosted user supplies their own EP-Online API key.

## Delivery plan

1. Establish repository, security, licensing, and contributor foundations.
2. Build and test PDOK address resolution.
3. Add BAG residential-unit and building retrieval.
4. Add EP-Online energy-performance retrieval using user-owned credentials.
5. Define normalized snapshots and provenance records.
6. Implement the first explainable comparison and conflict rules.
7. Add CBS and RIVM context with explicit geographic and status handling.
8. Generate JSON and PDF evidence reports.
9. Add the local web interface and side-by-side comparison experience.
10. Publish a documented first release and reproducible demo.

## Success criteria

- Two or more addresses can be compared from a single workflow.
- Every displayed value identifies its source and retrieval/reference time.
- Cross-register differences link to an explicit, tested explanation rule.
- Missing and provisional data remain visible.
- Reports can be reproduced from a stored snapshot and transformation version.
- The complete application runs locally without a hosted WoonLens account.
- CI verifies core clients, normalization, comparison, and report generation.
