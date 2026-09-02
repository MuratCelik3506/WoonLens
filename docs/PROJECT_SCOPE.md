# WoonLens Project Scope

## 1. Project Overview

WoonLens is a privacy-first, open-source application for comparing Dutch
residential properties using live official public data sources.

The application resolves user-selected addresses, retrieves property and
neighbourhood information from authoritative registries, preserves the
provenance and meaning of every value during the request, and can generate a
source-attributed download without retaining provider data on the server.

WoonLens is a data-auditing and decision-support tool. It does not provide
legal, financial, valuation, or building-inspection advice.

## 2. Problem Statement

Information about Dutch residential properties is distributed across multiple
public systems. These systems differ in identifiers, measurement definitions,
geographic scopes, update schedules, reference periods, data-quality
indicators, and licensing conditions.

Users can access individual facts, but it is difficult to determine:

- Which source produced a value
- When the value was retrieved or last updated
- Why two official sources show different values
- Whether data is missing, outdated, provisional, or conflicting
- Whether a value describes the property or only its surrounding area

WoonLens addresses this problem by creating transient source-backed property
views in memory and applying explicit comparison and validation rules.

## 3. Project Objectives

WoonLens will:

1. Resolve Dutch residential addresses to official BAG identifiers.
2. Retrieve property information from selected official sources.
3. Normalize source data without losing its original meaning.
4. Preserve source, timestamp, dataset, status, and transformation metadata.
5. Compare two to five residential properties.
6. Explain meaningful differences between official registers.
7. Distinguish missing data from zero values.
8. Identify stale, provisional, and potentially conflicting information.
9. Avoid persisting provider responses and derived property facts.
10. Export the current comparison as structured JSON or a readable PDF without
    server retention.
11. Support complete use without an account and optional accounts for saved
    searches, favourites, and comparison lists.
12. Re-fetch official data whenever a saved search or comparison is opened.
13. Use appropriately isolated credentials for authenticated services.

## 4. Target Users

The initial target users are:

- Homebuyers comparing candidate properties
- Renters evaluating residential options
- Expats navigating Dutch public property registers
- Residents reviewing public information about their address
- Researchers studying housing and public-data quality
- Civic-technology developers
- Inspectors and advisers preparing preliminary evidence

## 5. MVP Scope

### 5.1 Address Resolution

The MVP will:

- Accept a Dutch address search query.
- Return official address suggestions.
- Require the user to select the correct address.
- Resolve the selected address to official BAG address and addressable-object
  identifiers plus geographic coordinates.
- Preserve leading zeroes in official identifiers.
- Avoid inferring an address variant without user confirmation.

The primary search source is the current PDOK Location API. The selected result
is resolved through the fixed PDOK BAG OGC API address collection. Municipality,
district, and neighbourhood joins are separate contextual-data steps.

### 5.2 Property Data Retrieval

The MVP will retrieve the following Kadaster BAG information:

- Residential-unit and building identifiers
- Registered floor area
- Usage purposes and object status
- Construction year and building status
- Number of residential units where available

The MVP will retrieve the following EP-Online information:

- Registered energy label
- Registration date and validity information
- Building or thermal-zone measurements
- Relevant energy-performance metadata
- Available mutation or file metadata

The application must not treat BAG registered area and EP-Online thermal-zone
area as directly equivalent measurements.

### 5.3 Neighbourhood and Environmental Context

The MVP will include a limited and documented selection of:

- CBS neighbourhood geometry, housing statistics, selected demographic and
  energy context, dataset year, and table identifier.
- Luchtmeetnet/RIVM station metadata, selected air-quality observations,
  timestamps, pollutant identifiers, and data status where available.

Environmental observations must not be presented as exact property-level
measurements unless the source explicitly supports that interpretation.

### 5.4 Transient Normalized Property Views

Each address produces a normalized property view that exists only for the live
request. Every normalized value in that response must retain:

- Provider and dataset
- Source endpoint, table, or collection
- Original object identifier and source field
- Retrieval timestamp and reference period
- Source status
- Transformation rule and validation result
- Applicable attribution

Raw source responses are validated and transformed in memory. They are not
written to the application database, filesystem, logs, reports, or cache.

### 5.5 Property Comparison

Users will be able to compare between two and five addresses. The comparison
will show:

- Values by property and the source of each value
- Measurement definitions
- Retrieval and reference dates
- Missing-data and source-status indicators
- Explainable cross-source differences
- Potential conflicts requiring further investigation

The application will not produce a universal property score.

### 5.6 Validation and Conflict Rules

Validation rules must be explicit, deterministic, documented, versioned, and
independently testable. A difference between two sources must not automatically
be classified as an error.

Before reporting a conflict, the system must consider measurement definition,
geographic scope, reference date, registration status, data freshness, unit of
measurement, and missing-value conventions.

Validation results should use categories such as:

- Consistent
- Different definition
- Different reference period
- Missing
- Stale
- Provisional
- Potential conflict
- Unable to evaluate

### 5.7 Reports and Exports

The MVP will generate a machine-readable JSON evidence report and a basic
human-readable PDF evidence report.

Reports must include selected addresses, official identifiers, compared
values, source attribution, retrieval timestamps, dataset versions or years,
validation results, unavailable sources, known limitations, and WoonLens rule
versions.

Reports must not include API keys, authentication headers, signed URLs,
personal owner or resident information, or unnecessary raw source records.

### 5.8 Local Operation

The application will:

- Run locally using Docker Compose.
- Provide the complete comparison workflow without requiring an account.
- Allow optional accounts to save minimum search, favourite, and comparison
  references without saving provider facts.
- Inject provider credentials through the deployment environment.
- Avoid logging user address searches by default.
- Provide documented setup and health-check procedures.

### 5.9 Optional Accounts

Accounts are optional and do not unlock access to additional official property
facts. An account may store only user-owned organisation data needed to reopen a
search, favourite, or comparison. Opening a saved item always triggers new
provider requests.

The account store must not contain provider response fields, normalized
property facts, environmental observations, generated reports, or API caches.

The minimum reference schema, provider-neutral identity boundary, session
handling, ownership checks, export, deletion, and backup expiry are fixed by
[`ADR 0010`](adr/0010-oidc-bff-and-minimal-account-data.md). These controls do
not change the guest workflow or permit persistence of live provider facts.

## 6. Out of Scope

The following are explicitly excluded from the MVP:

- Property advertisement scraping or commercial listing integrations
- Owner or resident identification and personal-data enrichment
- Sale-price prediction or automated property valuation
- Mortgage recommendations
- Legal advice or building-inspection conclusions
- Structural safety assessments
- A universal or AI-generated property score
- Automatic ranking of properties as best or worst
- Native mobile applications
- Real-time collaboration
- Mandatory user accounts
- Bulk redistribution of restricted source data
- Provider-response caching or storage
- Historical property-fact timelines
- Automatic correction of upstream public records

These items require separate scope approval before implementation.

## 7. Initial Data Sources

| Source                | Purpose                                           | Authentication   |
| --------------------- | ------------------------------------------------- | ---------------- |
| PDOK Location API     | Address search and official BAG address reference | None             |
| Kadaster BAG via PDOK | Residential-unit and building records             | None             |
| EP-Online REST API    | Energy-performance records                        | Personal API key |
| CBS geometry via PDOK | Neighbourhood boundaries                          | None             |
| CBS StatLine OData    | Neighbourhood and housing statistics              | None             |
| Luchtmeetnet Open API | Current environmental observations                | None             |

Each integration must be implemented behind an isolated source-specific
client. Adding another source requires a documented use case, license and
authentication review, field mappings, provenance requirements, deterministic
test fixtures, and failure-handling rules.

## 8. Technical Scope

### Backend

The planned backend uses Python, FastAPI, Pydantic, and Pytest. It is
responsible for source clients, response validation, request-scoped
normalization, comparisons, downloads, account features, and health checks.

### Data Storage

PostgreSQL is planned only for optional accounts and minimum saved-search,
favourite, and comparison references. Provider payloads, normalized property
facts, comparison results, and generated reports are explicitly excluded. The
first vertical slice does not require a database.

### Frontend

The planned frontend uses TypeScript, Next.js, and MapLibre. It is responsible
for address selection, side-by-side comparison, source disclosures, warning
presentation, map context, and report downloads.

The frontend will be implemented only after the command-line vertical slice
proves the source and normalization workflow.

### Operations

The planned operational foundation consists of Docker Compose, GitHub Actions,
structured logs, automated tests, and health checks.

## 9. Security and Privacy Scope

The repository and application must not expose API keys, access tokens,
authentication cookies, signed URLs, real user search histories, owner or
resident information, or restricted bulk datasets.

Required controls include:

- Excluding local environment files from Git
- Redacted or synthetic test fixtures
- Secret scanning in CI
- Safe logging defaults
- Request timeouts and controlled retry behaviour
- Clear authentication errors
- Dependency and security updates

Security vulnerabilities must be reported privately when disclosure could
expose users, credentials, or infrastructure.

## 10. Data Licensing Scope

WoonLens source code is licensed under the MIT License. Third-party data
remains subject to its original terms, and WoonLens does not relicense upstream
data.

Before a source is included in a release, the project must document its
provider, applicable terms, attribution requirements, redistribution and
storage restrictions, authentication conditions, and review date. Datasets
with unclear redistribution rights must not be bundled with releases.

## 11. Quality Requirements

Every implementation task must include verification appropriate to its risk.
Expected test categories are:

- Unit and model-validation tests
- Transformation and comparison-rule tests
- Deterministic source-client tests using fixtures
- Contract tests
- Report-generation tests
- A small number of optional live integration tests

Live tests must be disabled by default, require explicit credentials where
necessary, avoid exposing sensitive response data, and never be required for
normal offline test execution.

## 12. Delivery Phases

### Phase 1 — Repository Foundation

Deliverables include project scope, contribution workflow, security and data
licensing policies, an environment template, initial API research, and GitHub
Issue and Pull Request conventions.

Exit criteria:

- Foundation documentation is merged into `main`.
- Initial milestones and Issues are defined.
- Secret-handling rules are established.

### Phase 2 — CLI Vertical Slice

Deliverables include the Python project structure, configuration handling,
PDOK address resolution, BAG and EP-Online retrieval, a transient normalized
property view, JSON output, and automated tests.

Exit criterion: one selected Dutch address produces a validated, source-backed
JSON view without persisting provider facts.

### Phase 3 — Comparison and Audit Engine

Deliverables include multi-address input, live comparison, a field
definition registry, validation and conflict rules, missing and stale-data
handling, and rule-version metadata.

Exit criterion: two or more addresses can be compared with explainable
results.

### Phase 4 — Context and Reporting

Deliverables include CBS and Luchtmeetnet/RIVM context, JSON and PDF evidence
reports, attribution, and limitation sections.

Exit criterion: a source-attributed JSON or PDF download can be generated for a
live comparison without server retention.

### Phase 5 — Local Web Application

Deliverables include the address-selection interface, side-by-side comparison,
source and warning displays, map context, report downloads, and a local Docker
Compose environment.

Exit criterion: the complete comparison workflow can be performed through a
local browser.

### Phase 6 — Release Readiness

Deliverables include CI, security checks, installation and operational
documentation, a final license review, demo fixtures, and a versioned release.

Exit criterion: the project can publish its first documented and reproducible
release.

### Phase 7 — Optional Account Organisation

Deliverables include account registration and deletion, explicit favourites,
named saved comparison lists, and live reruns using freshly retrieved official
data.

Exit criterion: signed-in users can organise address references without the
database containing provider facts, comparison results, generated reports, or
automatic search history.

## 13. GitHub Work Structure

Development follows these rules:

- One defined problem per GitHub Issue
- One branch per Issue
- One focused Pull Request per branch
- Acceptance criteria defined before implementation
- Automated tests or verification evidence included in the Pull Request
- Pull Requests linked with `Closes #<issue-number>`
- Changes merged only after acceptance criteria are satisfied

Recommended milestones:

1. `v0.1 — Repository Foundation`
2. `v0.2 — CLI Live Property View`
3. `v0.3 — Comparison Engine`
4. `v0.4 — Evidence Reports`
5. `v0.5 — Local Web Application`
6. `v1.0 — First Public Release`

## 14. MVP Success Criteria

The MVP is successful when:

- A user can select two or more valid Dutch addresses.
- Each address resolves to official BAG identifiers.
- Property information is retrieved from the selected official sources.
- Every displayed value identifies its source.
- Missing and provisional data remain visible.
- Different measurement definitions are not presented as direct conflicts.
- Comparison rules are explicit and tested.
- JSON and PDF evidence reports can be generated.
- Provider responses and derived property facts are absent from persistent
  storage after the request completes.
- The complete comparison works without an account, while signed-in users may
  save minimum search, favourite, and comparison references.
- No credentials or restricted datasets are included in the repository.
