# ADR 0004: Typed Errors and Structured Logging

- Status: Accepted
- Date: 2026-08-30

## Context

WoonLens coordinates providers with different authentication, availability,
rate-limit, validation, and not-found behaviour. A failure must be useful to a
user and operator without exposing credentials, addresses, signed URLs, or raw
provider payloads.

The product also evaluates differences between official datasets. A legitimate
difference or missing value is part of the evidence and must not be confused
with an application exception.

## Decision

WoonLens will use typed application errors, transport-specific error mapping at
entrypoints, and structured logging with explicit privacy controls.

### Error taxonomy

The initial application error hierarchy contains:

```text
WoonLensError
  ConfigurationError
  InputValidationError
  SourceError
    SourceAuthenticationError
    SourceNotFoundError
    SourceRateLimitError
    SourceUnavailableError
    SourceContractError
  PersistenceError
  ReportGenerationError
```

Source errors may carry safe metadata such as:

- Provider identifier
- Operation identifier
- Stable internal error code
- Upstream HTTP status where safe
- Whether the operation is retryable
- Suggested retry delay where provided

They must not carry credentials, authorization headers, signed URLs, raw
response bodies, or unredacted request URLs.

### Domain outcomes are not exceptions

Missing data, stale data, provisional data, different definitions, and
cross-source conflicts are typed domain results. They are represented through
models such as `MissingValue` and `ValidationResult`, not by throwing a
`SourceError` after a valid provider response.

Exceptions describe inability to execute or trust an operation. Domain results
describe what valid evidence means.

### Boundary translation

Application and domain code do not import HTTP or CLI error types.

- FastAPI translates safe application errors into RFC 9457 Problem Details
  responses using `application/problem+json`.
- The CLI translates the same errors into concise messages and stable exit
  codes.
- Unexpected exceptions produce a generic external error while retaining a
  server-side stack trace and correlation ID.

Initial CLI exit-code categories are:

| Exit code | Category |
| ---: | --- |
| `0` | Success, including disclosed partial contextual data |
| `2` | Invalid command or user input |
| `3` | Configuration or authentication failure |
| `4` | Requested source record not found |
| `5` | Temporary provider or rate-limit failure |
| `6` | Provider contract or data-integrity failure |
| `7` | Persistence or report-generation failure |
| `1` | Unexpected internal failure |

Exact codes become a public CLI contract once the first release is published.

## Logging

WoonLens will use `structlog` integrated with Python standard logging.

- Development defaults to human-readable console output.
- Containers, CI, and production-like operation emit JSON logs.
- Log events use stable event names rather than prose-only messages.
- A correlation ID is created or accepted at each entrypoint and propagated
  through the use case and adapters.
- Snapshot operations receive a separate operation ID where useful.
- Timestamps are timezone-aware UTC.
- Log levels follow consistent semantics.

### Safe event fields

Examples include:

- `event`
- `correlation_id`
- `operation_id`
- `provider`
- `operation`
- `duration_ms`
- `attempt`
- `http_status`
- `retryable`
- `result_category`

### Data excluded by default

Logs must not contain:

- Full or partial credentials
- Authorization and cookie headers
- Signed URLs
- Raw request or response bodies
- User-entered address text
- Postal codes and house numbers
- BAG or other property identifiers
- Generated reports or snapshot payloads
- Owner, resident, or user personal information

An identifier needed for operational grouping must use a documented,
non-reversible process-scoped representation and requires a specific use case.
It must not become a stable tracking identifier by accident.

## Trace and Disclosure Rules

- Expected typed errors are logged without stack traces at the boundary that
  handles them.
- Unexpected exceptions include a server-side stack trace.
- Stack traces and internal exception messages are never returned to API or CLI
  users in production mode.
- Logging failure must not change the business result.
- Redaction occurs before serialization and export.
- Health endpoints expose component status categories, not credentials,
  connection strings, provider bodies, or user queries.

## Consequences

### Positive

- API and CLI behaviour remains consistent.
- Operators can correlate a failed workflow without logging the property being
  investigated.
- Provider contract failures are distinguishable from temporary downtime.
- Valid data uncertainty remains visible instead of becoming a generic error.

### Costs

- Every adapter must translate provider behaviour into the shared taxonomy.
- Safe metadata and redaction require dedicated tests.
- Public error codes require backward-compatible maintenance after release.

## Rejected Alternatives

### Returning provider errors directly

Rejected because provider bodies are inconsistent, unstable, and may disclose
sensitive request details.

### Logging complete requests and responses for debugging

Rejected because address queries, credentials, signed URLs, and public-register
records create unacceptable privacy and security risks.

### Treating every unusual value as an exception

Rejected because missing and conflicting official data are central product
outcomes, not necessarily system failures.

## Revisit Conditions

Telemetry export, distributed tracing, and external error monitoring require a
separate privacy and retention review before adoption.
