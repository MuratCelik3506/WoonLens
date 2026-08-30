# ADR 0009: Stateless Provider Data and Optional Accounts

- Status: Accepted
- Date: 2026-08-30
- Supersedes: ADR 0005 where it requires persistent property snapshots or raw
  provider records

## Context

WoonLens compares homes using live responses from official providers. The
product does not need to build a second property registry, retain historical
provider facts, or require an account before a user can compare homes.

Persisting provider payloads or derived property facts would add privacy,
licensing, retention, staleness, correction, and security obligations without
supporting the core live-comparison experience.

Optional accounts are still useful for organising searches, favourites, and
comparison lists. That user-owned organisation data must remain separate from
the official facts retrieved when an item is opened.

## Decision

Provider responses and all property, neighbourhood, energy, and environmental
facts derived from them are request-scoped and are not persisted by WoonLens.

- Provider payloads are processed in memory.
- Normalized property views and comparison results are transient.
- Provider data is not written to the application database, filesystem, logs,
  report store, background jobs, analytics, or application cache.
- Opening or refreshing a comparison always retrieves current provider data.
- JSON and PDF outputs are generated on demand and streamed to the user; the
  server does not retain generated reports.
- The complete comparison workflow is available without an account.

## Optional Account Data

An account may store only the minimum user-owned organisation data required for
saved searches, favourite address references, named comparison lists, and
preferences entered directly by the user.

A saved item is a recipe for rerunning a search, not a saved copy of official
property facts. It must not contain BAG area, construction year, energy data,
CBS values, environmental observations, normalized comparison output, or raw
provider fields beyond the minimum reference required to rerun the search.

The exact minimum address-reference schema, retention period, deletion flow,
and consent language require a separate account-data decision before account
implementation.

## Transient Data Contract

The provider-independent typed models described by ADR 0005 remain useful as
in-memory contracts. Immutability applies during one request so rules cannot
silently overwrite source values.

`PropertySnapshot` is replaced in current terminology by
`TransientPropertyView`. It has no persistence identity and does not imply
history. Field-level source, unit, reference period, retrieval time, status, and
transformation metadata travel in the live response and optional download.

## Caching

Application-level provider-response caching is disabled by design. If rate
limits later make a cache appear necessary, introducing one requires a new ADR
covering provider terms, data classification, encryption, retention,
invalidation, disclosure, and deletion. It is not an implementation detail.

## Logging and Observability

Logs and telemetry contain safe operational metadata only. They exclude search
text, selected addresses, direct property identifiers, provider payloads,
normalized facts, and generated comparisons. Metrics aggregate operations and
failures without labels that identify a property or user search.

## Consequences

### Positive

- Users receive current official data whenever they run a comparison.
- WoonLens avoids becoming a stale shadow registry.
- Provider-data privacy, breach, licensing, correction, and deletion exposure is
  substantially reduced.
- Guest and account experiences share the same live comparison pipeline.

### Costs

- Saved comparisons require new provider calls whenever opened.
- WoonLens cannot provide historical property timelines from its own database.
- A past download cannot be regenerated later unless the user retained it and
  providers still return equivalent data.
- Provider downtime cannot be hidden behind stored results.

## Rejected Alternatives

### Persist normalized property snapshots

Rejected because history is not a core product requirement and persistence
would create staleness and data-governance obligations.

### Store raw payloads but delete them later

Rejected because temporary storage still creates security, retention, and
licensing responsibilities without a necessary product benefit.

### Require an account for comparison

Rejected because official-data comparison is the core product and must remain
accessible without identity or saved history.

## Revisit Conditions

Provider-data persistence or caching may be reconsidered only through a new ADR
and a corresponding product-scope change. Optional account storage must be
defined before account implementation and cannot weaken the provider-data rule.
