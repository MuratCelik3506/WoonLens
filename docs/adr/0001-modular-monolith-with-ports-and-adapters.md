# ADR 0001: Modular Monolith with Ports and Adapters

- Status: Accepted
- Date: 2026-08-30

## Context

WoonLens must coordinate several independent public-data providers, retain
source provenance, normalize unlike data models, evaluate explicit rules, and
serve both a command-line workflow and an HTTP API.

The source integrations will change independently, but the initial product is
developed and operated by one maintainer. Splitting the system into networked
microservices would introduce deployment, observability, consistency, and
failure-management costs before those boundaries need independent scaling or
ownership.

A conventional framework-oriented layout would create the opposite risk:
provider-specific HTTP and persistence details could leak into the comparison
domain and make source contracts difficult to test.

## Decision

WoonLens will be implemented as a modular monolith using ports-and-adapters
(hexagonal) architecture.

The application will have one deployable backend unit with two initial inbound
adapters:

- FastAPI HTTP API
- Command-line interface

The core is divided into explicit layers:

1. **Domain** — provider-independent entities, value objects, provenance,
   comparison rules, and domain errors.
2. **Application** — use cases, orchestration, transaction boundaries, and
   interfaces required from external systems.
3. **Adapters** — provider clients, persistence implementations, clocks, report
   renderers, and other infrastructure integrations.
4. **Entrypoints** — FastAPI routes, CLI commands, dependency composition, and
   runtime startup.

Dependencies point inward. The domain must not import FastAPI, HTTP clients,
database drivers, environment loaders, or provider response models.

Provider response models remain inside their adapters. They are converted into
application or domain models through explicit mappers. Raw responses and
normalized values remain separate.

## Initial Package Direction

```text
src/woonlens/
  domain/
    models/
    provenance/
    rules/
    errors.py
  application/
    ports/
    services/
    commands/
    queries/
  adapters/
    sources/
      pdok/
      bag/
      ep_online/
      cbs/
      luchtmeetnet/
    persistence/
    reporting/
  entrypoints/
    api/
    cli/
  bootstrap/
tests/
  unit/
  contract/
  integration/
  fixtures/
```

This is a dependency map, not permission to create empty placeholder modules.
Directories are introduced when the first real implementation requires them.

## Boundary Rules

- Domain code has no infrastructure or framework dependencies.
- Application use cases depend on ports, never concrete adapters.
- Adapters may depend on application ports and domain types.
- Entrypoints translate transport input into application commands or queries.
- API routes and CLI commands must not contain business rules.
- One source adapter must not call another source adapter directly.
- Cross-source coordination belongs to an application service.
- Database models must not become domain models by default.
- Provider payloads must not be returned directly through the public API.
- Dependency construction is explicit in the bootstrap layer.

## Consequences

### Positive

- CLI and HTTP workflows reuse identical application logic.
- Provider behaviour can be tested behind deterministic contracts.
- Source changes remain isolated from the comparison domain.
- Persistence can change without rewriting domain rules.
- The system remains one operational unit while retaining extraction paths for
  future services.

### Costs

- Explicit mapping code is required between provider, application, and domain
  models.
- Boundaries require review discipline and architecture tests.
- Some small features will involve more files than in a framework-first layout.

These costs are accepted because traceability and source isolation are core
product requirements.

## Rejected Alternatives

### Microservices from the first release

Rejected because the project does not yet need independent deployment,
scaling, or team ownership. Network boundaries would increase operational
complexity without strengthening the data model.

### Framework-first layered application

Rejected because organizing the system around routes, ORM models, and utility
modules would allow provider and persistence concerns to leak into the domain.

### CLI-only prototype with disposable architecture

Rejected because the first vertical slice must become the foundation of the
product. The CLI is an inbound adapter, not a temporary second implementation.

## Revisit Conditions

This decision should be revisited only when a module requires independent
scaling, release cadence, security isolation, availability, or team ownership.
Extraction must be supported by operational evidence rather than speculative
future growth.
