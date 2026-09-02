# ADR 0010: OIDC BFF and Minimal Account Data

- Status: Accepted
- Date: 2026-09-02
- Extends: ADR 0003 and ADR 0009

## Context

WoonLens already provides the complete live-comparison journey to guests.
Optional accounts may organise favourites and named comparison lists, but they
must not turn WoonLens into an identity provider or property-data store.

Authentication affects the Next.js browser boundary, FastAPI authorization,
Docker development, PostgreSQL, deletion, backups, and incident response. One
contract is required before authentication or persistence is implemented.

## Decision

WoonLens uses a provider-neutral OpenID Connect (OIDC) boundary. A conforming
provider owns registration, authentication, multifactor authentication, and
recovery. WoonLens never receives or stores passwords or recovery secrets.

The web application uses OAuth Authorization Code with PKCE `S256`. The
deployment allow-lists discovery metadata, issuer, client identifier, audience,
redirect URI, and key set. Redirect URIs use exact matching. The callback
validates issuer, state, nonce, PKCE, signature, audience, expiry, and issued-at
claims. Implicit and resource-owner-password flows are prohibited.

### Browser and BFF boundary

Next.js acts as a Backend for Frontend (BFF):

1. A same-origin route starts sign-in with transaction-specific state, nonce,
   and PKCE values.
2. The callback validates the transaction and exchanges the code server-side.
3. Provider tokens remain in an encrypted, expiring server-side session store.
4. The browser receives only an opaque random session handle.
5. The BFF attaches the short-lived access token when forwarding an
   authenticated request to FastAPI.

Tokens must not enter application JavaScript, `localStorage`, `sessionStorage`,
IndexedDB, URLs, analytics, or client logs.

The production cookie is `__Host-woonlens_session` with `Secure`, `HttpOnly`,
`SameSite=Lax`, and `Path=/`, without a `Domain` attribute. `Lax` permits the
top-level OIDC return and is defence in depth, not the only CSRF control. Local
HTTP development uses a separate development cookie and cannot weaken
production settings.

Session identifiers rotate after authentication and privilege-relevant
changes. Logout revokes server state and expires the cookie. Absolute and idle
timeouts are mandatory and configurable. Refresh-token rotation is required
when refresh tokens are issued.

State-changing requests require a session-bound CSRF token and validation of
`Origin` plus Fetch Metadata where supported.

### API identity and authorization

FastAPI validates signature, allowed algorithm, issuer, API audience, expiry,
not-before, required scope, and key identifier. Unknown values fail closed. Key
discovery has bounded caching and refresh and never bypasses validation.

OIDC `iss` and `sub` together form the external identity. Email, name, and
provider username are not ownership keys. WoonLens maps the pair to a random
internal account UUID.

Every account repository operation derives its owner from verified credentials;
a client-supplied account ID is never trusted. Owner filtering occurs in the
query for every read, rename, run, export, and delete. Foreign and missing
objects produce the same not-found response. Random UUIDs do not replace
object-level authorization.

Guest endpoints stay public and must not create sessions, tracking identifiers,
or automatic history.

## Stored Data Contract

PostgreSQL may contain only these application-owned records.

### `account`

| Field        | Purpose                            |
| ------------ | ---------------------------------- |
| `id`         | Random internal ownership UUID     |
| `issuer`     | Exact configured OIDC issuer       |
| `subject`    | Opaque OIDC subject                |
| `created_at` | Account-organisation creation time |

`(issuer, subject)` is unique. Email, profile fields, passwords, recovery data,
and provider tokens are excluded.

### `favourite_address_reference`

| Field             | Purpose                                        |
| ----------------- | ---------------------------------------------- |
| `id`              | Random record UUID                             |
| `account_id`      | Owner reference                                |
| `pdok_address_id` | Minimum opaque UUID needed for live resolution |
| `created_at`      | Explicit user-action time                      |

`(account_id, pdok_address_id)` is unique. Display address, coordinates, BAG
facts, and source metadata are not retained.

### `saved_comparison`

| Field        | Purpose                                            |
| ------------ | -------------------------------------------------- |
| `id`         | Random record UUID                                 |
| `account_id` | Owner reference                                    |
| `name`       | Length-limited, untrusted, user-supplied list name |
| `created_at` | Creation time                                      |
| `updated_at` | Last explicit organisation change                  |

### `saved_comparison_address_reference`

| Field                 | Purpose                                        |
| --------------------- | ---------------------------------------------- |
| `saved_comparison_id` | Parent list reference                          |
| `position`            | User-defined order from 0 to 4                 |
| `pdok_address_id`     | Minimum opaque UUID needed for live resolution |

A comparison has two to five unique references. Application and database
constraints enforce ownership, uniqueness, size, and order.

The PDOK UUID is retained only when the user explicitly asks WoonLens to
remember a rerunnable reference. It is not a property fact or snapshot. If it
no longer resolves, WoonLens reports the reference as unavailable and offers
removal; it never falls back to stale facts.

### Prohibited persistence

Account storage, identity metadata, logs, analytics, queues, and application
caches must not contain:

- display addresses, coordinates, postal codes, or BAG object details;
- energy, area, construction, administrative, environmental, or CBS facts;
- provider responses, normalized views, comparisons, explanations, or audits;
- generated reports, automatic history, or unsubmitted selections;
- passwords, recovery secrets, ID tokens, access tokens, or refresh tokens.

The encrypted session store is the only exception for short-lived provider
credentials. It is an expiring authentication mechanism, not an account or
property-data store.

## Saved-Item Execution

Opening a favourite resolves its current PDOK UUID. Running a saved comparison
passes its ordered UUIDs to the same application service used by guests. BAG,
EP-Online, CBS, and Luchtmeetnet data are fetched again for every run.

Write endpoints never accept a live comparison payload. A failed rerun does not
mutate its saved recipe.

## Data Lifecycle

Records remain only while the user keeps the optional account. No automatic
inactivity deletion is introduced without reliable notice and a new decision.

Users can export the four stored record types as JSON. Export performs no live
provider lookup and therefore contains no property snapshot.

Deletion requires recent authentication and explicit confirmation:

1. block new authenticated writes;
2. revoke all WoonLens sessions;
3. transactionally delete favourites, list references, lists, and the account;
4. end or unlink OIDC state and explain whether the external provider account
   remains separate;
5. emit only an anonymous outcome metric.

WoonLens cannot promise to delete a social or independently owned identity
account. A dedicated managed tenant may add deletion through a separately
tested adapter.

Primary rows disappear immediately after the successful transaction. Encrypted
backups expire within 35 days. Restoration must replay a protected deletion
ledger before data becomes available; ledger entries use keyed digests and
expire after the last affected backup. They contain no email, address reference,
or provider fact.

On local deletion failure the transaction rolls back, mutation remains blocked,
and the response is generic and retryable. Logs contain a correlation ID and
failure class, never identity or saved content.

## Threat Controls

| Threat                      | Required control                                                     |
| --------------------------- | -------------------------------------------------------------------- |
| Code interception/injection | Authorization Code, PKCE `S256`, exact redirect, state and nonce     |
| XSS token theft             | BFF, server-side token storage, opaque HttpOnly cookie, CSP          |
| CSRF                        | Bound token, Origin/Fetch Metadata checks, SameSite defence in depth |
| Session fixation/replay     | Cryptographic handles, rotation, expiry, revocation                  |
| Account enumeration         | Provider-owned recovery and generic local errors                     |
| Broken object authorization | Owner-scoped queries and negative cross-account tests                |
| Identity confusion          | Exact `(issuer, subject)` key; no email auto-linking                 |
| Malicious names             | Limits, parameterized writes, contextual output encoding             |
| Provider/JWKS failure       | Authentication fails closed; guest journey remains available         |
| Secret leakage              | Server-only typed configuration, scans, redacted logs                |

Rate limits cover sign-in initiation, callbacks, export, and deletion.

## Local Development and Testing

Account implementation adds a standards-compatible local OIDC provider,
PostgreSQL, and a disposable session store to Docker Compose. It uses synthetic
users and non-production keys that production configuration must reject.

Pull-request tests need no cloud account, personal credential, email delivery,
or public network. They cover:

- invalid issuer, audience, signature, expiry, nonce, state, and PKCE;
- cookie flags, rotation, logout, CSRF, and session expiry;
- cross-account operations and owner-scoped not-found behaviour;
- constraints, cascading deletion, and backup/deletion contract tests;
- rejection of provider facts and result payloads in saved writes;
- fresh live comparison invocation when a saved item runs;
- unchanged anonymous guest journeys.

## Privacy and Operations

Identity mapping, list names, address references, and timestamps are personal
data in context. The product explains their purpose before account creation and
offers export and deletion. Collection follows explicit account actions only.

Production requires a privacy notice, processor and transfer assessment for the
selected OIDC/hosting providers, documented backups, secret rotation, TLS,
monitoring, and incident response. This engineering decision is not legal
advice.

## Consequences

### Positive

- WoonLens does not own password or recovery implementation.
- Browser JavaScript cannot read provider tokens.
- OIDC providers remain replaceable outside the domain.
- Account data stays minimal, explicit, exportable, and deletable.
- Guest and saved comparisons share one live pipeline.

### Costs

- Production needs an OIDC provider and expiring session store.
- CSRF, token validation, key rotation, and deletion add operations.
- Saved items must tolerate removed addresses and provider downtime.
- Backup deletion needs a tested restoration process.

## Rejected Alternatives

- **First-party passwords:** rejected because hashing, recovery, MFA, mail, and
  abuse prevention are not WoonLens product differentiators.
- **Browser-stored tokens:** rejected because JavaScript-readable bearer tokens
  increase XSS impact and complicate revocation.
- **Next.js-only checks:** rejected because FastAPI owns account use cases and
  must authorize independently.
- **Email ownership keys:** rejected because email changes and can be recycled;
  OIDC defines issuer and subject as the stable pair.
- **Saved labels or snapshots:** rejected because they weaken the minimum
  reference boundary and create stale provider-derived state.

## Revisit Conditions

A new ADR is required for linked identity providers, roles/organisations, native
clients, offline API access, non-OIDC deployment, a different address-reference
authority, or provider-data caching. Selecting a concrete OIDC vendor is a
deployment review and cannot silently weaken this contract.

## References

- [RFC 9700: OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700)
- [RFC 10017: OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0-18.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP API1:2023 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- [EU General Data Protection Regulation](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
