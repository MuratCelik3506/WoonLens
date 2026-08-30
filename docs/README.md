# WoonLens Documentation

This directory contains the product, data, engineering, and architectural
contracts for WoonLens.

## Product and Delivery

| Document | Purpose |
| --- | --- |
| [`PROJECT_SCOPE.md`](PROJECT_SCOPE.md) | Authoritative MVP boundaries, delivery phases, and success criteria |
| [`PRODUCT_FEATURE_MAP.md`](PRODUCT_FEATURE_MAP.md) | Guest and account journeys, screens, use cases, information architecture, and delivery order |
| [`../PROJECT_PROPOSAL.md`](../PROJECT_PROPOSAL.md) | Product problem, audience, differentiation, and high-level direction |
| [`../README.md`](../README.md) | Repository overview and entry point |

## Data Sources

| Document | Purpose |
| --- | --- |
| [`DATA_JOURNEY.md`](DATA_JOURNEY.md) | Narrative explanation of how one address moves through the source chain |
| [`DATA_SOURCE_API.md`](DATA_SOURCE_API.md) | Verified endpoints, request examples, fields, joins, and failure behaviour |
| [`DATA_LICENSING.md`](DATA_LICENSING.md) | Third-party terms, attribution, storage, and redistribution boundaries |

## Engineering

| Document | Purpose |
| --- | --- |
| [`SOFTWARE_ENGINEERING.md`](SOFTWARE_ENGINEERING.md) | Runtime, architecture, data contracts, testing, CI, workflow, and Definition of Done |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Contributor-facing branch, commit, pull-request, data, and quality rules |
| [`../SECURITY.md`](../SECURITY.md) | Private vulnerability reporting and credential-exposure response |

## Architecture Decision Records

Architecture Decision Records preserve the context, decision, consequences,
rejected alternatives, and revisit conditions for durable engineering choices.

| ADR | Decision |
| --- | --- |
| [`0001`](adr/0001-modular-monolith-with-ports-and-adapters.md) | Modular monolith with ports and adapters |
| [`0002`](adr/0002-async-io-with-synchronous-domain.md) | Asynchronous I/O with a synchronous domain |
| [`0003`](adr/0003-typed-configuration-and-secret-isolation.md) | Typed configuration and secret isolation |
| [`0004`](adr/0004-typed-errors-and-structured-logging.md) | Typed errors and structured logging |
| [`0005`](adr/0005-immutable-data-contracts-and-field-provenance.md) | Immutable data contracts and field-level provenance |
| [`0006`](adr/0006-layered-deterministic-testing.md) | Layered and deterministic testing |
| [`0007`](adr/0007-automated-quality-gates.md) | Automated quality gates |
| [`0008`](adr/0008-issue-driven-pull-request-workflow.md) | Issue-driven pull-request workflow |
| [`0009`](adr/0009-stateless-provider-data-and-optional-accounts.md) | Stateless provider data and optional accounts |

## Authority and Change Rules

- `PROJECT_SCOPE.md` is authoritative for what the MVP includes and excludes.
- `SOFTWARE_ENGINEERING.md` is authoritative for the current engineering
  standard.
- ADRs explain why durable decisions were made; a later ADR supersedes rather
  than silently rewrites an accepted decision.
- Data-source behaviour must be checked against official provider documentation
  and optional live verification before implementation or release.
- Third-party terms must be reviewed before new storage, caching, hosted demo,
  bulk ingestion, or redistribution behaviour is introduced.
- Documentation changes follow the same Issue, pull-request, verification, and
  Definition of Done workflow as code changes.
