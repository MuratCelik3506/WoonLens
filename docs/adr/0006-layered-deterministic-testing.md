# ADR 0006: Layered and Deterministic Testing

- Status: Accepted
- Date: 2026-08-30

## Context

WoonLens depends on external APIs whose availability, payloads, rate limits,
and records can change independently. Tests that depend on live services would
be slow, non-deterministic, and require personal credentials. Tests based only
on mocked happy paths would fail to protect identifier handling, missing-value
semantics, pagination, provenance, and provider contract boundaries.

The project therefore needs several test layers with explicit responsibilities.

## Decision

WoonLens will use a layered, deterministic testing strategy:

```text
Unit
  -> Contract
  -> Integration
  -> End-to-end
  -> Optional live smoke
```

The default local and pull-request test suite must run without network access,
personal credentials, or a developer's `.env` file.

## Tooling

- `pytest` is the test runner.
- AnyIO's pytest integration runs asynchronous tests.
- `respx` provides deterministic `httpx` request and response contracts.
- `Hypothesis` provides property-based tests for suitable invariants.
- `import-linter` verifies architectural dependency rules.
- `coverage.py` through `pytest-cov` measures line and branch coverage.
- FastAPI entrypoints are tested through `httpx` ASGI transport or the
  framework test client where synchronous behaviour is intentional.
- CLI tests execute the command boundary and assert exit-code and output
  contracts.

## Test Layers

### Unit tests

Unit tests cover domain value objects, normalization, provenance, validation
rules, application decisions, and individual mappings.

They do not use the network, filesystem, wall clock, random global state,
environment variables, or a real database unless the unit is specifically an
adapter for that boundary. Clocks, ID generators, source ports, and repositories
are injected.

### Source contract tests

Every provider adapter has deterministic contract fixtures covering at least:

- Successful response
- Empty successful response
- Invalid request and validation response
- Authentication failure where applicable
- Not found
- Rate limiting and `Retry-After`
- Timeout and connection failure
- Upstream `5xx`
- Pagination where applicable
- Nullable fields and provider missing-value sentinels
- Removal or incompatible type of a required field
- Addition of an unused field
- Unknown enum value

Fixtures are synthetic, minimized, redacted, or explicitly licensed for
redistribution. Each fixture documents its origin and transformation status.

### Integration tests

Integration tests verify real boundaries under local control, including:

- Repository implementations against a disposable PostgreSQL/PostGIS container
- Database migrations
- FastAPI dependency composition
- Application orchestration with deterministic fake or recorded source ports
- Report storage and retrieval

Integration tests must create isolated state and clean it without relying on
test execution order.

### End-to-end tests

End-to-end tests exercise supported CLI and HTTP workflows through the composed
application. External providers remain deterministic substitutes unless a test
is explicitly marked live.

They verify user-visible results, stable error shapes, exit codes, snapshot
creation, and report generation.

### Live smoke tests

Live provider checks use `@pytest.mark.live` and are excluded from default test
runs. They:

- Require explicit opt-in.
- Use credentials only when the provider requires them.
- Validate status and selected schema properties rather than storing full
  responses.
- Avoid assertions on volatile real-world values.
- Never run as a required pull-request check.
- May run on a controlled schedule with provider-specific limits and secret
  access.

## Property-Based Testing

Hypothesis is used where invariants matter more than a few examples, including:

- Official identifier validation and leading-zero preservation
- Missing-value and zero separation
- Unit and percentage-scale conversions
- Date and timezone boundaries
- Ordering and selection of multiple registrations
- Rule symmetry or monotonicity where the domain rule promises it
- Serialization round trips for stable contracts

Generated failures must be reproducible through Hypothesis' example database
or the minimized failing example reported by the test.

## Report Verification

JSON and PDF outputs require deterministic inputs. JSON contracts use semantic
object comparisons and selected golden files. PDF tests compare extracted
content and rendered layout rather than volatile binary metadata alone.

Golden files are reviewed artifacts, not a shortcut for understanding a large
diff. Intentional changes require an explicit update and review.

## Coverage Policy

- The initial overall line and branch coverage floor is 90 percent.
- Critical normalization, missing-value, provenance, and validation modules
  target 100 percent branch coverage.
- New or changed code must not reduce the configured floor.
- Exclusions require a documented reason and must not hide reachable business
  logic.
- Coverage does not replace assertions, boundary cases, property tests, or
  review.

The threshold may be adjusted only through a documented decision based on the
actual codebase, not to make a failing pull request pass.

## Test Quality Rules

- Tests follow arrange, act, assert or another consistently readable structure.
- A test explains one behaviour even when several assertions describe that
  behaviour.
- Tests do not depend on execution order.
- Time, randomness, and generated IDs are controlled.
- Retries and concurrency use deterministic fakes where possible.
- Sensitive values are checked by negative assertions to confirm they do not
  appear in logs, errors, snapshots, or reports.
- Bug fixes include a regression test that fails without the fix.

## Consequences

### Positive

- Pull-request checks remain fast, repeatable, and credential-free.
- Provider behaviour and schema assumptions are explicit.
- Critical evidence transformations receive stronger assurance than ordinary
  glue code.
- Live availability checks do not destabilize normal development.

### Costs

- Maintaining representative fixtures and contract cases requires ongoing work.
- Property tests and deterministic concurrency tests require careful design.
- Disposable database integration adds container execution time.

## Rejected Alternatives

### Live APIs in the default test suite

Rejected because availability, records, credentials, and rate limits would make
pull requests non-deterministic.

### Unit tests only

Rejected because mappings, migrations, dependency composition, and user-facing
contracts require real boundary verification.

### Coverage as the sole quality target

Rejected because executed lines do not prove correct assertions, contract
coverage, or meaningful edge cases.

## Revisit Conditions

Coverage floors and test distribution should be reviewed after the first
vertical slice provides real execution-time and defect data. Any change must
preserve deterministic required checks and explicit live-test isolation.
