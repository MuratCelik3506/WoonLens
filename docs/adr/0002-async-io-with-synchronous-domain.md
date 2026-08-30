# ADR 0002: Asynchronous I/O with a Synchronous Domain

- Status: Accepted
- Date: 2026-08-30

## Context

Creating one WoonLens snapshot requires multiple network requests. Some
requests are sequential because one response provides the identifier needed by
the next request, while other source calls become independent after address
resolution.

Executing all independent requests serially would add upstream latencies
together. Making the entire codebase asynchronous, including pure models and
comparison rules, would spread transport concerns into code that performs no
I/O and make domain tests unnecessarily complex.

## Decision

WoonLens will use asynchronous I/O at infrastructure and application
boundaries while keeping domain logic synchronous and side-effect free.

- FastAPI handlers will be asynchronous.
- External HTTP adapters will use `httpx.AsyncClient`.
- Application use cases may be asynchronous when they coordinate I/O ports.
- The CLI will invoke the same asynchronous use cases through `anyio.run()`.
- Domain models, normalization calculations, and comparison rules will remain
  synchronous unless they perform genuine I/O.
- Independent provider calls may run concurrently through structured
  concurrency with explicit limits.

## Execution Shape

```text
PDOK suggest -> user selection -> PDOK lookup
                                      |
                                      +--> BAG unit -> BAG building(s)
                                      +--> EP-Online
                                      +--> CBS geometry
                                      +--> CBS StatLine metadata/observations
                                      +--> station discovery/measurements
```

Only calls whose inputs are already known and whose behaviour is independent
may run concurrently. Required identifier chains remain sequential.

## Reliability Rules

- Every outbound call has an explicit connect, read, write, and pool timeout.
- A request-scoped total time budget prevents one snapshot from waiting
  indefinitely across several retries.
- Concurrency is bounded globally and per provider.
- Cancellation propagates from the entrypoint to in-flight provider calls.
- Retries apply only to explicitly transient and idempotent operations.
- Retries use bounded exponential backoff with jitter.
- Authentication, validation, and not-found responses are not retried.
- Provider rate limits and `Retry-After` instructions are respected.
- One optional contextual-source failure does not cancel successful property
  facts unless the use case declares that source required.
- Shared HTTP clients are created during application startup and closed during
  shutdown; a new client is not created for every request.

Exact timeout, retry, and concurrency values will be configuration with tested
defaults rather than unexplained constants inside adapters.

## Consequences

### Positive

- Independent provider latency can overlap.
- FastAPI and CLI share the same orchestration implementation.
- Cancellation and total time budgets can be propagated coherently.
- Domain tests remain fast and do not require an event loop.

### Costs

- Adapter and application tests must cover asynchronous failure behaviour.
- Concurrency can amplify rate-limit pressure if provider-specific limits are
  omitted.
- Shared client lifetime and shutdown require explicit bootstrap management.

## Rejected Alternatives

### Fully synchronous execution

Rejected because serial calls would unnecessarily increase snapshot latency
and consume server workers while waiting on upstream services.

### Async everywhere

Rejected because domain calculations and rules do not benefit from asynchronous
syntax. Making them async would couple pure logic to an execution mechanism.

### Unbounded parallel requests

Rejected because it would make upstream rate limits, connection pools, and
local resource use unpredictable.

## Revisit Conditions

The model should be revisited if profiling shows CPU-bound normalization or
report generation blocking the event loop. CPU-heavy work may then move to a
bounded worker pool or job system without changing domain semantics.
