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

Concrete source, persistence, and report adapters
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
  adapters/        # Source APIs, persistence, and report implementations
  entrypoints/     # FastAPI and CLI transport concerns
  bootstrap/       # Explicit dependency construction and startup
```

Every external data provider receives its own adapter and raw response models.
Source adapters do not call one another directly. Cross-source workflows belong
to application services and operate through declared ports.

### Enforcement

- Architecture boundaries will be checked by automated import rules.
- Provider payloads will not be exposed directly through public API responses.
- Persistence models will remain separate from domain models unless an explicit
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
WOONLENS_EP_ONLINE_API_KEY
WOONLENS_HTTP_TOTAL_TIMEOUT_SECONDS
WOONLENS_HTTP_MAX_CONCURRENCY
WOONLENS_DATABASE_URL
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
snapshot payloads by default. Redaction happens before serialization.

## 6. Data and Provenance Contracts

### Decision

WoonLens uses immutable, provider-independent domain contracts with field-level
provenance. The detailed contract is recorded in
[`ADR 0005`](adr/0005-immutable-data-contracts-and-field-provenance.md).

- Domain entities and value objects use frozen dataclasses and enums.
- Provider payloads use adapter-local Pydantic models.
- Persistence models and public API schemas remain separate.
- Raw provider responses and normalized evidence are separate records.
- Explicit, tested mappers connect every boundary.

### Snapshot contract

`PropertySnapshot` is immutable after creation. A refresh creates a new
snapshot rather than mutating historical evidence. It contains address
identity, property and energy facts, neighbourhood and environmental context,
source records, validation results, and an explicit schema version.

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

Snapshots retain independent schema, adapter-contract, transformation, rule,
and report versions. Raw payload retention and physical storage require a
separate decision before persistence implementation.

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
- Disposable PostgreSQL/PostGIS containers for persistence integration

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

| Concern | Tool |
| --- | --- |
| Format and Python lint | Ruff |
| Strict static typing | mypy |
| Architecture boundaries | import-linter |
| Tests and branch coverage | pytest and pytest-cov |
| Dependency vulnerabilities | pip-audit |
| Secret detection | gitleaks |
| Dockerfile quality | hadolint |
| GitHub Actions validity | actionlint |
| Markdown consistency | markdownlint |
| Fast local checks | pre-commit |
| Dependency update proposals | Dependabot |

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

Initial milestones are `v0.1 — Repository Foundation`, `v0.2 — CLI Property
Snapshot`, `v0.3 — Comparison Engine`, `v0.4 — Evidence Reports`, `v0.5 — Local
Web Application`, and `v1.0 — First Public Release`.

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
- Raw source records and normalized evidence remain separate.
- Validation results reference rather than overwrite source evidence.
- License, attribution, storage, retention, and redistribution implications are
  reviewed for affected data.

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
implementation introduces concrete persistence, raw-retention, reporting,
deployment, and operational requirements.
