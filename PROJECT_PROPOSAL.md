# WoonLens — Project Proposal

## One-line summary

WoonLens is a privacy-first, open-source tool for comparing Dutch homes with
live facts from official public sources.

## Problem

Dutch housing information is distributed across several official systems.
These systems use different identifiers, reference dates, geographic levels,
and measurement definitions. A homebuyer or renter can find individual facts,
but cannot easily answer:

- Which official source produced this value?
- When was it last updated?
- Why do two registers show different areas or construction details?
- Which facts are property-level and which describe only the surrounding area?
- Can the current result be understood without trusting an opaque score?

Existing address dashboards usually aggregate values into cards. They rarely
turn source differences, uncertainty, and provenance into a first-class product.

## Proposed solution

A user enters two or more Dutch residential addresses. WoonLens resolves their
official identifiers, requests data from selected public sources, and
normalizes the responses in memory for a live comparison.

The system then applies explicit validation rules. It distinguishes genuine
conflicts from values that differ because they describe different concepts. For
example, a BAG registered area and an EP-Online thermal-zone area may both be
correct while using different measurement scopes.

The result is a transparent due-diligence evidence pack containing:

- A side-by-side property comparison
- Source-level facts and missing-data indicators
- Explainable warnings and cross-register differences
- Retrieval dates and source provenance
- A source-attributed JSON or PDF download generated on demand
- Clear disclosure that official data is refreshed when the comparison is run

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
4. Avoid persisting provider responses or derived property facts.
5. Produce an on-demand export that records how and when the current result was
   obtained, without retaining the export on the server.
6. Support full comparison without an account and optional accounts for saved
   searches, favourites, and comparison lists.

## Initial data sources

| Source | Purpose |
| --- | --- |
| PDOK Location API + BAG address detail | Address search, CRS84 coordinates, and official BAG identifiers |
| Kadaster BAG | Buildings, residential units, registered area, usage, and construction year |
| EP-Online | Registered energy-performance facts and thermal-zone measurements |
| CBS Open Data | Neighbourhood-level housing and demographic context |
| RIVM/Luchtmeetnet | Environmental measurements with provisional/ratified status |

Every integration remains isolated behind a source-specific client. Upstream
responses are mapped into a normalized model without discarding original
identifiers or provenance.

## MVP scope

The authoritative implementation boundaries, delivery phases, and acceptance
criteria are maintained in [`docs/PROJECT_SCOPE.md`](docs/PROJECT_SCOPE.md).

### Included

- Address search and normalization
- Comparison of two to five addresses
- Live BAG and EP-Online property facts
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
    -> normalize transient property views in memory
    -> evaluate definitions, freshness, and conflicts
    -> compare homes side by side
    -> optionally download the current comparison
```

## Architecture direction

- **Backend:** Python and FastAPI
- **Validation:** Pydantic models and explicit rule objects
- **Database:** PostgreSQL for optional accounts and minimum saved-search,
  favourite, and comparison references; never provider facts
- **Frontend:** TypeScript, Next.js, and MapLibre
- **Execution:** Request-scoped live source retrieval with no provider-data
  persistence or background synchronization
- **Testing:** Pytest, deterministic fixtures, contract tests, and limited live smoke tests
- **Operations:** Docker Compose, GitHub Actions, structured logs, and health checks

The first implementation milestone will be a command-line vertical slice. It
must resolve one real address and produce a transient, source-backed JSON view
without writing provider facts to a database or local cache.

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
minimal redacted examples. It will not contain personal API keys, provider
responses, address-search logs, restricted bulk exports, or source datasets
whose redistribution terms have not been confirmed.

Each self-hosted user supplies their own EP-Online API key.

## Delivery plan

1. Establish repository, security, licensing, and contributor foundations.
2. Build and test PDOK address resolution.
3. Add BAG residential-unit and building retrieval.
4. Add EP-Online energy-performance retrieval using an isolated,
   deployment-managed credential.
5. Define transient normalized views and request-scoped provenance records.
6. Implement the first explainable comparison and conflict rules.
7. Add CBS and RIVM context with explicit geographic and status handling.
8. Generate non-retained JSON and PDF comparison downloads.
9. Add the web interface and side-by-side comparison experience.
10. Publish a documented first release and deterministic synthetic demo.

## Success criteria

- Two or more addresses can be compared from a single workflow.
- Every displayed value identifies its source and retrieval/reference time.
- Cross-register differences link to an explicit, tested explanation rule.
- Missing and provisional data remain visible.
- Provider responses and derived property facts are absent from persistent
  storage after a request completes.
- The complete comparison works without an account; signing in adds only saved
  searches, favourites, and comparison organisation.
- CI verifies core clients, normalization, comparison, and report generation.
