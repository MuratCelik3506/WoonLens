# ADR 0003: Typed Configuration and Secret Isolation

- Status: Accepted
- Date: 2026-08-30

## Context

WoonLens runs in containers and connects to public services with different
timeouts, limits, and authentication requirements. EP-Online requires a
personal API key, while future persistence and deployment environments may add
database credentials and other secrets.

Untyped environment lookups spread across modules would make configuration
failures appear late, allow inconsistent defaults, and increase the chance of
secrets entering logs or unrelated components.

## Decision

WoonLens will use one typed configuration model built with
`pydantic-settings`.

- Application environment variables use the `WOONLENS_` prefix.
- `.env` loading is a local-development convenience only.
- Containers and CI receive configuration through environment variables or
  platform-provided secret mounts.
- Secrets use `SecretStr` or an equivalent non-revealing type.
- Required configuration is validated once during startup.
- Invalid or missing required configuration causes startup to fail with a
  useful message that does not include secret values.
- Settings are created in the bootstrap layer and passed explicitly to the
  components that require them.
- Modules must not construct settings during import or read environment
  variables directly.

## Namespace

The `WOONLENS_` prefix identifies values owned by this application and avoids
collisions with generic host or container variables.

Initial names include:

```text
WOONLENS_ENVIRONMENT
WOONLENS_LOG_LEVEL
WOONLENS_EP_ONLINE_API_KEY
WOONLENS_HTTP_TOTAL_TIMEOUT_SECONDS
WOONLENS_HTTP_MAX_CONCURRENCY
WOONLENS_DATABASE_URL
```

Only settings required by implemented behaviour will be added to the example
file. A documented future setting is not automatically an active runtime
requirement.

## Precedence

From highest to lowest priority:

1. Explicit values passed by a test or application bootstrap
2. Process environment variables
3. Local `.env` file when local-development loading is enabled
4. Safe defaults declared by the settings model

Production must not depend on a copied `.env` file inside the image.

## Secret Boundaries

- The EP-Online credential is passed only to the EP-Online adapter.
- Database credentials are passed only to the persistence adapter and migration
  process.
- Secret values must not appear in object representations, structured logs,
  traces, metrics labels, errors, health responses, reports, fixtures, or test
  snapshots.
- Authorization headers and signed URLs are redacted by key name and value
  pattern before logging.
- Secret values are never build arguments and are never copied into container
  layers.
- `.env.example` contains names and safe non-secret examples only.

## Environment Behaviour

Development, test, and production use the same settings schema. Environment
selection may choose safe operational defaults, but it must not silently alter
domain rules or data interpretation. Behaviour changes require explicit typed
settings and tests.

Test configuration is supplied explicitly and must not depend on a developer's
real `.env` file.

## Consequences

### Positive

- Configuration errors fail at startup rather than during a user request.
- Settings are discoverable and type checked.
- Components receive only the configuration they need.
- Secret exposure through generic configuration dumps is less likely.
- Docker, CI, and local development share one contract.

### Costs

- Bootstrap code must map the root settings object into component-specific
  configuration.
- Tests must construct explicit settings instead of relying on ambient host
  variables.

## Rejected Alternatives

### Direct `os.environ` access throughout the application

Rejected because it hides dependencies, delays validation, and makes tests
dependent on ambient process state.

### Committed environment files per deployment

Rejected because environment files are easy to leak and do not integrate well
with deployment secret stores.

### Passing the complete settings object to every module

Rejected because it grants unnecessary access to secrets and couples unrelated
components to global configuration.

## Revisit Conditions

This decision may be extended when a deployment platform provides a dedicated
secret manager. The typed settings interface and component-level secret
isolation must remain intact.
