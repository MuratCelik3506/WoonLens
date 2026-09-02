# WoonLens Software Engineering Handbook

## Purpose

This handbook defines how WoonLens is designed, implemented, tested, reviewed,
and operated. It records the project's shared engineering rules so that
technical decisions remain consistent as the codebase grows.

The handbook is intentionally developed before application implementation.
Material architectural decisions that require more context will also receive a
short Architecture Decision Record (ADR).

## 1. Runtime and Dependency Management

### Decision

WoonLens will use:

- Python 3.13
- `uv` for Python dependency and virtual-environment management
- `pyproject.toml` as the Python project and tool configuration file
- `uv.lock` for reproducible dependency resolution
- A `src/woonlens` package layout
- `.python-version` to declare the local Python version

### Docker-first development

Docker is the canonical application runtime. Development, tests, and production-
like local execution must be available through containers so contributors do
not need to reproduce the complete toolchain directly on their workstation.

`uv` will be used inside the Python build stage to install the locked dependency
set. Installing `uv` on the host is recommended for fast editor integration and
local commands, but it is not required to run the project.

The project will provide:

- A multi-stage `Dockerfile`
- A `compose.yaml` local development environment
- A non-root application user in the runtime image
- A container health check
- Separate development and production-oriented targets where their needs differ
- A `.dockerignore` that excludes credentials, caches, local data, and generated
  artifacts

### Reproducibility rules

- The Python minor version must be explicit in the container base image.
- Runtime dependencies must be declared in `pyproject.toml` and locked in
  `uv.lock`.
- CI must install from the lock file rather than resolving unconstrained
  dependencies.
- The committed lock file and container build must be sufficient to reproduce
  the supported environment.
- Application secrets must be injected at runtime and must never be copied into
  an image layer.

### Initial package layout

```text
src/
  woonlens/
tests/
pyproject.toml
uv.lock
.python-version
Dockerfile
compose.yaml
```

The internal package structure will be defined separately after the application
architecture and service boundaries are agreed.

## 2. Application Architecture

### Decision

WoonLens will use a modular monolith with ports-and-adapters architecture. The
decision and its trade-offs are recorded in
[`ADR 0001`](adr/0001-modular-monolith-with-ports-and-adapters.md).

The initial system is one deployable backend with two inbound adapters:

- A FastAPI HTTP API
- A command-line interface

Both entrypoints call the same application use cases. Neither entrypoint owns
business rules.

### Dependency direction

```text
FastAPI / CLI
      |
      v
Application use cases and ports
      |
      v
Domain models, provenance, and rules

Concrete source, account persistence, and report-streaming adapters
      |
      +---- implement application ports
      +---- map external models into internal models
```

Dependencies point inward. The domain must not import frameworks, HTTP clients,
database drivers, environment loaders, or provider-specific response models.

### Module boundaries

```text
src/woonlens/
  domain/          # Provider-independent models and rules
  application/     # Use cases, orchestration, commands, queries, ports
  adapters/        # Source APIs, account persistence, and report streaming
  entrypoints/     # FastAPI and CLI transport concerns
  bootstrap/       # Explicit dependency construction and startup
```

Every external data provider receives its own adapter and raw response models.
Source adapters do not call one another directly. Cross-source workflows belong
to application services and operate through declared ports.

### Enforcement

- Architecture boundaries will be checked by automated import rules.
- Provider payloads will not be exposed directly through public API responses.
- Account persistence models remain separate from domain models unless an explicit
  decision demonstrates that combining them is safe.
- New networked services will require evidence of independent scaling,
  availability, security, release, or ownership requirements.

## 3. Execution and Concurrency Model

### Decision

WoonLens will use asynchronous I/O with a synchronous, side-effect-free domain.
The full decision is recorded in
[`ADR 0002`](adr/0002-async-io-with-synchronous-domain.md).

- FastAPI handlers and external HTTP adapters are asynchronous.
- Source clients use shared `httpx.AsyncClient` instances.
- The CLI invokes the same application use cases through `anyio.run()`.
- Domain models, calculations, and comparison rules remain synchronous.
- The home-overview application service resolves the address once, runs
  independent provider calls concurrently, and sequences neighbourhood metrics
  after administrative context because that join has a real data dependency.
- Partial success catches only typed `WoonLensError` source outcomes; unexpected
  exceptions remain visible to error monitoring instead of being mislabeled as
  missing data.
- The live comparison service bounds fan-out to two through five unique homes,
  starts their overview workflows concurrently, and preserves input order in
  the response.
- Comparison interpretations are deterministic, side-effect-free application
  rules with stable IDs and an explicit rules version. They describe evidence
  and uncertainty but do not generate an overall winner.
- Independent source calls may run concurrently only through bounded structured
  concurrency.

### Reliability requirements

Every outbound integration must define:

- Connect, read, write, and pool timeouts
- A request-scoped total time budget
- Global and provider-specific concurrency limits
- Cancellation behaviour
- Retryable status and exception categories
- Bounded exponential backoff with jitter
- Rate-limit and `Retry-After` handling

Authentication, request-validation, and not-found responses are not retried.
Optional contextual-source failures are represented explicitly and do not erase
successfully retrieved required property facts.

Shared clients are constructed and closed by the bootstrap layer. Adapters must
not create a new HTTP client for every request.

## 4. Configuration and Secret Management

### Decision

WoonLens will use a single typed `pydantic-settings` model with a `WOONLENS_`
environment-variable prefix. The complete decision is recorded in
[`ADR 0003`](adr/0003-typed-configuration-and-secret-isolation.md).

Settings are validated once during bootstrap and then reduced to the
component-specific configuration required by each adapter. Modules must not
read environment variables directly or create settings objects during import.

### Environment contract

```text
WOONLENS_ENVIRONMENT
WOONLENS_LOG_LEVEL
WOONLENS_PDOK_LOCATION_API_URL
WOONLENS_PDOK_BAG_API_URL
WOONLENS_PDOK_CBS_NEIGHBORHOODS_API_URL
WOONLENS_PDOK_CBS_REGIONS_API_URL
WOONLENS_CBS_ADMINISTRATIVE_DATASET_YEAR
WOONLENS_CBS_STATLINE_API_URL
WOONLENS_CBS_NEIGHBORHOOD_INDICATORS_DATASET_ID
WOONLENS_CBS_NEIGHBORHOOD_INDICATORS_DATASET_YEAR
WOONLENS_HTTP_CONNECT_TIMEOUT_SECONDS
WOONLENS_HTTP_READ_TIMEOUT_SECONDS
WOONLENS_HTTP_WRITE_TIMEOUT_SECONDS
WOONLENS_HTTP_POOL_TIMEOUT_SECONDS
WOONLENS_ADDRESS_SUGGESTION_LIMIT
WOONLENS_BAG_MAX_RELATED_BUILDINGS
WOONLENS_EP_ONLINE_API_URL
WOONLENS_EP_ONLINE_API_KEY
```

Only variables required by implemented functionality belong in
`.env.example`. Development, test, and production use the same typed schema.
Tests supply configuration explicitly and do not load a developer's `.env`.

### Secret rules

- `.env` is a local-development convenience and is never committed.
- Docker and CI inject configuration at runtime.
- Secrets use non-revealing types such as `SecretStr`.
- Missing required settings fail application startup without revealing values.
- EP-Online credentials are visible only to the EP-Online adapter.
- Secrets, authorization headers, and signed URLs are excluded from logs,
  traces, metrics labels, errors, health output, reports, and fixtures.
- Secrets are never Docker build arguments or image-layer content.

## 5. Error Model and Logging

### Decision

WoonLens uses typed application errors and structured, privacy-preserving logs.
The complete taxonomy and boundary behaviour are recorded in
[`ADR 0004`](adr/0004-typed-errors-and-structured-logging.md).

The error taxonomy distinguishes configuration, input, source authentication,
not-found, rate-limit, temporary availability, source-contract, persistence,
and report-generation failures.

Valid evidence outcomes such as missing values, stale data, provisional data,
different definitions, and potential conflicts are domain results rather than
exceptions.

### Entrypoint mapping

- FastAPI maps safe application errors to RFC 9457 Problem Details responses.
- The CLI maps the same errors to concise messages and stable exit-code
  categories.
- Application and domain modules do not import transport-specific error types.
- Unexpected errors return a generic external message and retain a server-side
  trace linked by correlation ID.

### Structured logging

WoonLens uses `structlog` with Python standard logging integration.

- Development output is human-readable; container and CI output is JSON.
- Events use stable names and timezone-aware UTC timestamps.
- Correlation and operation IDs are propagated through use cases and adapters.
- Safe operational fields include provider, operation, duration, attempt,
  status, retryability, and result category.
- Expected typed errors do not produce stack traces; unexpected failures do.

Logs exclude credentials, authentication headers, signed URLs, raw bodies,
address text, postal codes, house numbers, property identifiers, reports, and
transient comparison payloads by default. Redaction happens before
serialization.

## 6. Data and Provenance Contracts

### Decision

WoonLens uses immutable, provider-independent, request-scoped domain contracts
with field-level provenance. The original contract is recorded in
[`ADR 0005`](adr/0005-immutable-data-contracts-and-field-provenance.md) and its
stateless correction in
[`ADR 0009`](adr/0009-stateless-provider-data-and-optional-accounts.md).

- Domain entities and value objects use frozen dataclasses and enums.
- Provider payloads use adapter-local Pydantic models.
- Optional account models and public API schemas remain separate.
- Raw provider responses and normalized evidence remain separate in memory and
  are discarded after the request.
- Explicit, tested mappers connect every boundary.

### Transient property-view contract

`TransientPropertyView` is immutable during a request. It contains address
identity, property and energy facts, neighbourhood and environmental context,
source metadata, validation results, and an explicit response-schema version.
It has no persistence identity or historical lifecycle.

Every normalized fact uses a `SourcedValue[T]` carrying its value state, unit,
source reference, reference period, retrieval time, source status, and
transformation reference.

### Evidence rules

- Official identifiers are typed strings and preserve leading zeroes.
- Date-times are timezone-aware and stored in UTC.
- A source-local date is not assigned an invented time zone.
- Evidence-sensitive decimal values use `Decimal`.
- Units and percentage scales are explicit.
- `None` alone does not describe why data is unavailable.
- Missing reasons distinguish not found, not published, not applicable,
  redacted, source unavailable, invalid at source, and unknown.
- Validation results reference evidence and never overwrite source values.

### Contract evolution

Unused new provider fields do not fail ingestion. Removal or incompatible type
changes of required fields produce a `SourceContractError`. Unknown source enum
values are retained for review instead of being silently mapped to an unrelated
internal value.

Live responses retain independent response-schema, adapter-contract,
transformation, rule, and download-schema versions. Provider payloads,
normalized facts, comparison results, and generated reports are not persisted.

The frontend validates and presents comparison insights and source audits but
does not recreate interpretation rules from raw values. Stable rule identifiers,
classifications, affected address references, compared fields, and rule version
remain visible through progressive disclosure. Selection changes invalidate the
entire result and its explanations together so rule output cannot be attached to
stale evidence.

The optional map is split into a client-only dynamic chunk and loads only after
explicit user action. Its MapLibre worker and shared module are copied from the
installed package into a same-origin public directory before development and
production builds. The Docker development image grants only that public
directory and `.next` to its unprivileged Node user; the production image copies
the generated public worker assets explicitly. Textual spatial evidence remains
the required fallback and does not depend on WebGL or the tile host.

Per-home detail panels are projected from the overview already embedded in the
live-comparison response. The frontend allowlists the displayed BAG, EP-Online,
CBS, and Luchtmeetnet fields instead of rendering arbitrary provider payloads.
Property, building, neighbourhood, and monitoring-station levels remain explicit;
technical identifiers use progressive disclosure. Opening a detail panel performs
no network request, and a selection change invalidates its details with the rest
of the transient comparison.

JSON evidence reports are produced by an application service over the existing
live comparison use case. A timezone-aware clock is injected for deterministic
tests. The HTTP adapter owns JSON serialization, the attachment filename, and
the `Cache-Control: no-store` response header; the domain and application layers
remain unaware of FastAPI. Report schema versions and comparison rule versions
are separate because either contract can evolve independently.

Luchtmeetnet integration downloads the three bounded official metadata
catalogues concurrently, filters ended locations and series, and selects at
most one station per supported pollutant. Measurement requests are deduplicated
by station identifier. This keeps the request below the documented public API
fair-use limit without application persistence or cross-request caching.
Great-circle selection is deterministic; station distance, type, measurement
window, and `current-unratified` status remain part of the evidence contract.

The PDF renderer is an outbound adapter behind the application-level
`PdfReportRenderer` protocol. ReportLab remains outside the domain and
application layers. The API selects the renderer and owns HTTP media type,
filename, and cache headers. Renderer tests use an invariant PDF canvas and an
injected report clock so equal evidence produces deterministic bytes. Text
extraction checks document content, while Poppler page rendering and visual
inspection verify layout quality that extraction cannot prove.

### Persistence boundary

PostgreSQL may store optional accounts and minimum user-owned saved-search,
favourite, and comparison references. Opening a saved item always invokes the
live provider pipeline. The exact account reference schema, retention, consent,
and deletion contract are defined by
[`ADR 0010`](adr/0010-oidc-bff-and-minimal-account-data.md). Authentication uses
a provider-neutral OIDC boundary: Next.js acts as a BFF, browser JavaScript
never receives provider tokens, and FastAPI independently validates credentials
and enforces owner-scoped access. PostgreSQL stores only the account identity
mapping, explicit favourite address UUIDs, and named ordered comparison recipes.

The implemented account foundation uses an Alembic-managed PostgreSQL account
table with a unique OIDC issuer/subject pair. Favourite-address persistence
extends that boundary with an
owner-scoped opaque PDOK UUID only. Listing never exposes the owner identity,
duplicate saves are idempotent, deletion is owner-scoped, and reopening calls
the live address adapter instead of reading a stored label or property fact.
Named comparisons retain only a length-limited name and two to five ordered,
unique PDOK address UUIDs. Rename, run, and delete queries are owner-scoped;
running a saved recipe calls the existing live comparison service and stores no
result.
The Next.js BFF performs
Authorization Code + PKCE and stores short-lived credentials encrypted with
AES-256-GCM in Redis behind hashed opaque handles. FastAPI validates the
asymmetric JWT signature, issuer, audience, lifetime, and required scope before
mapping the external identity. Keycloak supplies synthetic local OIDC behaviour
in Compose; it is not the selected production identity provider.

## 7. Testing Strategy

### Decision

WoonLens uses layered, deterministic tests. The complete policy is recorded in
[`ADR 0006`](adr/0006-layered-deterministic-testing.md).

```text
Unit -> Contract -> Integration -> End-to-end -> Optional live smoke
```

The required local and pull-request suite runs without network access, personal
credentials, or a developer's `.env` file.

### Tools

- `pytest` for test execution
- AnyIO pytest support for asynchronous tests
- `respx` for deterministic `httpx` contracts
- `Hypothesis` for property-based tests
- `import-linter` for architecture boundaries
- `pytest-cov` and `coverage.py` for line and branch coverage
- Disposable PostgreSQL containers for optional account persistence integration

### Required coverage

Every source adapter covers success, empty response, invalid input,
authentication where applicable, not found, rate limiting, timeout, upstream
failure, pagination, nullable values, contract changes, and unknown enum values.

Live tests are explicitly marked, disabled by default, and never required for a
pull request. They assert stable status and schema properties rather than
volatile real-world values.

The initial overall line and branch coverage floor is 90 percent. Critical
normalization, missing-value, provenance, and validation modules target 100
percent branch coverage. Coverage supplements rather than replaces meaningful
assertions and boundary tests.

Fixtures must be synthetic, minimized, redacted, or explicitly redistributable,
and must document their origin and transformation status. JSON and PDF report
tests use deterministic inputs and reviewed semantic or golden outputs.

## 8. Code Quality and CI Gates

### Decision

WoonLens enforces automated local and pull-request quality gates. Tool choices,
security constraints, and suppression rules are recorded in
[`ADR 0007`](adr/0007-automated-quality-gates.md).

| Concern                     | Tool                  |
| --------------------------- | --------------------- |
| Format and Python lint      | Ruff                  |
| Strict static typing        | mypy                  |
| Architecture boundaries     | import-linter         |
| Tests and branch coverage   | pytest and pytest-cov |
| Dependency vulnerabilities  | pip-audit             |
| Secret detection            | gitleaks              |
| Dockerfile quality          | hadolint              |
| GitHub Actions validity     | actionlint            |
| Markdown consistency        | markdownlint          |
| Fast local checks           | pre-commit            |
| Dependency update proposals | Dependabot            |

### Required pull-request checks

```text
lock validation
  -> format and lint
  -> strict type check
  -> architecture contracts
  -> unit, contract, and integration tests
  -> coverage threshold
  -> dependency and secret audits
  -> Docker build and smoke test
```

All required checks must pass before merge. CI uses repository-owned commands
that can also be run locally. The initial supported runtime is Python 3.13; no
speculative multi-version matrix is used.

### Exceptions and supply-chain rules

- Suppressions are narrow, justified, and linked to an Issue when temporary.
- Quality thresholds are not lowered simply to pass a pull request.
- Vulnerability exceptions record advisory, exposure, mitigation, owner, and
  review date.
- GitHub Actions are pinned to immutable commit SHAs where practical.
- CI permissions follow least privilege.
- Required pull-request jobs receive no personal provider credentials.
- Dependabot pull requests undergo the same review and checks as other changes.
- Docker verification includes locked installation, non-root execution, safe
  startup, health behaviour, and build-context exclusions.

## 9. GitHub Work Management

### Decision

WoonLens uses an Issue-driven, one-branch, one-pull-request workflow. The full
workflow and solo-maintainer trade-offs are recorded in
[`ADR 0008`](adr/0008-issue-driven-pull-request-workflow.md).

```text
Backlog -> Ready -> In Progress -> In Review -> Done
```

An Issue is ready only when its problem, goal, scope, exclusions, acceptance
criteria, verification plan, dependencies, and relevant data or security impact
are defined. One maintainer should normally keep no more than two Issues in
progress.

### Branch and commit convention

Branches use `<type>/<issue-number>-<short-description>`, for example
`feat/12-pdok-client` or `fix/27-label-selection`.

Commit subjects use an imperative conventional prefix such as `feat:`, `fix:`,
`test:`, `docs:`, `refactor:`, or `chore:`. Commits remain focused and exclude
unrelated cleanup, credentials, restricted data, and local artifacts.

### Pull requests and merge

Every pull request addresses one primary Issue, includes `Closes #<number>`,
records verification and impact, and receives a full self-review. All required
checks and acceptance criteria must pass, and conversations must be resolved.

`Squash and merge` is the normal merge method. The squash title follows the
commit convention and the source branch is deleted after merge.

### Default branch protection

The default branch requires a pull request, required status checks, resolved
conversations, and protection from force push and deletion. An independent
approval is not required while the project has one maintainer. At least one
approval becomes required when another active contributor joins.

Initial milestones are `v0.1 — Repository Foundation`, `v0.2 — CLI Live Property
View`, `v0.3 — Comparison Engine`, `v0.4 — Comparison Downloads`, `v0.5 — Web
Application`, and `v1.0 — First Public Release`.

## 10. Definition of Done

An Issue is Done only when the delivered outcome, evidence, documentation, and
operational consequences satisfy this section. Writing code or opening a pull
request is not completion.

### Scope and behaviour

- Every acceptance criterion is satisfied and demonstrably verified.
- The observable user or system outcome matches the Issue goal.
- Unrelated work is excluded from the pull request.
- Incomplete or newly discovered work has a linked follow-up Issue.
- The pull request does not describe partial delivery as completion.

### Architecture and implementation

- The change respects the ports-and-adapters dependency rules.
- Domain code remains independent of frameworks, providers, and persistence.
- Provider, domain, persistence, and public transport models remain separate.
- First-party code satisfies strict typing and configured lint rules.
- Suppressions, exclusions, and temporary compatibility paths are narrow and
  justified.
- Debug output, dead code, unexplained constants, and temporary artifacts are
  removed.

### Data and provenance

- Every new normalized field has a documented provider and source-field map.
- Units, reference periods, retrieval time, source status, and transformation
  version are retained.
- Missing data remains distinct from zero, empty, and not applicable.
- Property, neighbourhood, municipality, and monitoring-station facts are
  labelled at their actual level.
- Raw provider payloads and normalized facts remain separate in memory and
  neither is persisted after the request.
- Validation results reference rather than overwrite source evidence.
- License, attribution, transient processing, and redistribution implications
  are reviewed for affected data.

### Tests and verification

- New behaviour has appropriate unit tests.
- Source-adapter changes include deterministic contract tests.
- Bug fixes include a regression test that fails without the fix.
- Required integration and end-to-end paths are covered.
- Relevant invalid, unauthorized, not-found, rate-limit, timeout, upstream
  failure, pagination, and contract-change behaviours are verified.
- Coverage thresholds pass, including critical branch-coverage requirements.
- Required tests run without network access or personal credentials.
- Exact verification commands and results are recorded in the pull request.

### Security and privacy

- No credential, signed URL, authentication header, private key, or restricted
  payload is present in code, history, artifacts, logs, reports, or fixtures.
- Logs exclude address text, postal codes, house numbers, direct property
  identifiers, and raw payloads by default.
- Fixtures are synthetic, minimized and redacted, or explicitly reusable.
- New dependencies and changed container layers pass configured security gates.
- Secrets and settings are passed only to components that require them.
- Security-sensitive behaviour fails closed and does not reveal internals.

### Documentation and public contracts

- User, contributor, API, CLI, configuration, and operational documentation is
  updated when behaviour changes.
- Material architectural decisions have an accepted ADR.
- New implemented environment variables appear in `.env.example` with safe
  guidance and no real value.
- New or changed sources document access, joins, fields, missing values, failure
  behaviour, terms, and attribution.
- Links, commands, schemas, and examples are verified.
- Compatibility or migration impact is explicitly described.

### CI, review, and merge readiness

- Every required CI check passes.
- The pull request links its primary Issue with `Closes #<number>`.
- The pull request description accurately records scope, verification, risks,
  data impact, and limitations.
- The author reviews the complete diff.
- Review conversations are resolved.
- The branch satisfies the default-branch merge policy.
- The squash title follows the commit convention.

### Operations and recovery

- Configuration changes have safe defaults or explicit startup validation.
- Database migrations are tested and their deployment order is documented.
- Health, readiness, logging, timeout, and partial-result behaviour are reviewed
  where affected.
- Risky changes describe a practical rollback or forward-recovery path.
- Known operational limitations have owners or linked follow-up Issues.

### Not Done

An Issue is not Done when any required condition is deferred without a scoped,
linked follow-up that preserves the original acceptance criteria. In
particular, the following are not acceptable completion states:

- Tests or documentation will be added later.
- Raw provider responses are temporarily exposed as public models.
- Missing values are represented as zero or an unexplained empty value.
- Required CI depends on a personal API credential.
- Coverage or type safety is weakened only to make the change pass.
- A known limitation is mentioned without a tracked follow-up.
- Only part of the Issue goal is implemented while the Issue is closed.

## Decisions Still to Define

The initial engineering foundation is complete. New decisions will be added as
implementation introduces account persistence, report streaming, deployment,
and operational requirements.
