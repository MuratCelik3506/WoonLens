# ADR 0005: Immutable Data Contracts and Field-Level Provenance

- Status: Accepted
- Date: 2026-08-30

## Context

WoonLens combines facts from sources that use different identifiers, units,
measurement scopes, reference periods, status values, and missing-value
conventions. A normalized value without its source context would make a report
impossible to audit and could turn valid definitional differences into false
conflicts.

Provider payloads, database rows, domain evidence, and public API responses also
serve different purposes. Reusing one model across all boundaries would leak
provider and persistence concerns into the domain.

## Decision

WoonLens will use immutable, provider-independent domain contracts with
field-level provenance.

- Domain entities and value objects use frozen standard-library dataclasses,
  enums, and explicit domain types.
- Domain models do not depend on Pydantic, FastAPI, an ORM, or provider SDKs.
- Provider payload models are validated with Pydantic inside their adapters.
- Persistence records and public API schemas are separate models with explicit
  mappings.
- Raw provider responses and normalized evidence are stored separately and
  connected through stable source-record references.

## Core Aggregate

The initial normalized aggregate is `PropertySnapshot`:

```text
PropertySnapshot
  snapshot_id
  schema_version
  created_at
  address_identity
  property_facts
  energy_facts
  neighbourhood_context
  environmental_context
  source_records
  validation_results
```

A snapshot is immutable after creation. Refreshing data creates another
snapshot; it does not mutate historical evidence.

## Sourced Values

Every normalized fact is represented by a generic sourced value rather than a
bare primitive:

```text
SourcedValue[T]
  value_state
  value or missing_reason
  unit
  source_reference
  reference_period
  retrieved_at
  source_status
  transformation_reference
```

`value_state` makes the value/missing distinction explicit. Exactly one of
`value` and `missing_reason` is present.

The source reference identifies:

- Provider and dataset
- Endpoint, collection, table, and measure where applicable
- Original source object and field
- Raw source-record ID
- Applicable attribution

The transformation reference identifies the mapping or calculation name and
version that produced the normalized value.

## Missing Values

`None` alone is not a sufficient evidence state. Initial missing reasons are:

```text
NOT_FOUND
NOT_PUBLISHED
NOT_APPLICABLE
REDACTED
SOURCE_UNAVAILABLE
INVALID_AT_SOURCE
UNKNOWN
```

Provider-specific sentinel values are converted into a typed missing reason
while the original representation remains available in the raw source record.
Missing values are never converted to numeric zero, an empty string, or a
misleading default.

## Primitive and Identifier Rules

- Official identifiers are validated strings and retain leading zeroes.
- Identifiers from different namespaces use distinct value-object types.
- Date-times are timezone-aware and normalized to UTC for storage.
- A source-local date without a time zone remains a date or explicitly
  qualified local value; a time zone is never invented.
- Decimal measurements use `Decimal` when binary floating-point rounding could
  alter evidence or report output.
- Every measured value has an explicit unit defined by a controlled unit type.
- Percentages retain their declared scale; fractions and percentages are not
  silently interchanged.
- Source-language labels may be preserved alongside controlled internal enums.

## Raw Source Records

A `RawSourceSnapshot` records the evidence received from one provider
operation:

```text
RawSourceSnapshot
  source_record_id
  provider
  operation
  retrieved_at
  upstream_status
  content_type
  payload_checksum
  safe_request_fingerprint
  adapter_contract_version
  payload_reference
```

The safe request fingerprint excludes credentials, signed query parameters,
and direct address or property identifiers. Raw payload retention is subject to
the provider's terms, privacy policy, and a future retention decision.

Checksums are integrity aids, not proof that upstream data is authoritative or
unchanged. The payload storage mechanism is an adapter concern.

## Versions

Snapshots retain independent versions for:

- Snapshot schema
- Source adapter contract
- Normalization transformation
- Validation and comparison rules
- Report schema where exported

Version identifiers must be stable and interpretable by the application. A Git
commit may be recorded as supporting metadata but is not the only schema
version.

## Provider Contract Evolution

Provider models parse only documented fields used by WoonLens and retain the
raw payload separately where permitted.

- A new unused upstream field does not fail normal ingestion.
- Removal of a required field is a `SourceContractError`.
- An incompatible type or invalid required identifier is a
  `SourceContractError`.
- A nullable documented field remains nullable.
- Contract tests compare selected live response shapes without storing
  sensitive live payloads.
- Unknown enum values are retained as source values and surfaced for mapping;
  they are not silently assigned to an unrelated internal category.

## Validation Results

Cross-source evaluation produces immutable `ValidationResult` records. Each
result includes:

- Rule identifier and version
- Category and severity
- References to the sourced values evaluated
- Human-readable explanation key and safe parameters
- Evaluation timestamp
- Outcome such as consistent, different definition, different period, missing,
  stale, provisional, potential conflict, or unable to evaluate

Validation never overwrites the underlying sourced values.

## Mapping Boundaries

```text
Provider JSON
    -> adapter response model
    -> explicit normalization mapper
    -> immutable domain evidence
    -> application result
    -> explicit API / CLI / report schema
```

Every arrow is testable. Provider models and ORM models are never returned
directly from a public entrypoint.

## Consequences

### Positive

- Every displayed value can answer where it came from and how it was produced.
- Historical snapshots remain reproducible and comparable.
- Missing data and conflicting definitions remain explicit.
- Provider, domain, storage, and public contracts can evolve independently.
- Validation rules can reference exact evidence rather than copied primitives.

### Costs

- Explicit mapping code is required at every boundary.
- Field-level provenance increases storage and model complexity.
- Schema and rule versions require lifecycle discipline.

These costs are accepted because provenance and explainability are core product
capabilities rather than optional metadata.

## Rejected Alternatives

### Flat normalized dictionaries

Rejected because they lose type safety, missing reasons, provenance, and
versioned transformations.

### Pydantic models throughout the domain

Rejected because the domain must remain independent of validation and transport
framework choices.

### One model for API, database, and domain

Rejected because it couples public compatibility, persistence design, and
provider evolution.

### Mutable snapshots

Rejected because modifying historical evidence would make comparisons and
reports non-reproducible.

## Revisit Conditions

The physical raw-payload storage and retention policy must be decided before
persistence implementation. The immutable domain and provenance requirements
remain unless the product's audit objective changes.
