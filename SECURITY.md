# Security Policy

## Project status

WoonLens is currently in early development and has no supported production
release. Security-sensitive findings are still important, especially those
involving credentials, data redistribution, request logging, or generated
reports.

## Reporting a vulnerability

Do not open a public GitHub issue for a vulnerability that could expose:

- API keys, tokens, cookies, or signed URLs
- Personal or user-submitted address data
- Private infrastructure details
- Restricted bulk source data
- A practical method for abusing an upstream public-data service

Use GitHub's private vulnerability reporting feature when it is available for
this repository. If it is not available, contact the repository maintainer
privately through their GitHub profile and establish a private reporting
channel before sharing sensitive details.

For non-sensitive bugs, open a normal GitHub issue with reproducible steps and
redacted examples.

## Credential exposure

If a real credential is committed or posted:

1. Revoke or rotate it immediately at the issuing service.
2. Remove it from the current repository state.
3. Review logs and usage for unauthorized access.
4. Treat Git history cleanup as secondary; deletion from a branch does not make
   an exposed credential safe again.

Never include a real secret in an issue, pull request, screenshot, fixture,
example response, or generated report.

## Browser boundary

The frontend sends restrictive content-security, framing, MIME-sniffing,
referrer, and browser-permission headers. MapLibre workers are copied from the
pinned npm dependency and served from the WoonLens origin. The content-security
policy permits map connections only to the documented OpenFreeMap tile host;
camera, microphone, and geolocation access are disabled. The map uses official
address coordinates already present in the transient comparison and does not
request browser geolocation.

## Optional account boundary

Optional accounts use the provider-neutral OIDC and Backend-for-Frontend
contract in
[`ADR 0010`](docs/adr/0010-oidc-bff-and-minimal-account-data.md). WoonLens does
not store passwords or recovery secrets, and browser JavaScript must never
receive provider tokens. Production sessions use an opaque, rotating
`Secure`, `HttpOnly`, `SameSite=Lax` host-only cookie plus explicit CSRF
protection.

FastAPI independently validates the configured issuer and audience and applies
owner-scoped authorization to every saved object operation. Account tables may
contain only the identity mapping and explicitly saved organisation recipes.
They exclude provider facts, address labels, comparison results, reports, and
automatic search history. Account export, session revocation, deletion, and the
maximum 35-day encrypted-backup expiry are part of the security boundary.
The JSON export deliberately excludes OIDC issuer/subject values, provider
tokens, address labels, provider responses, and generated reports. Destructive
account deletion requires an authenticated, exact same-origin BFF request;
session state is removed only after the owner-scoped database deletion succeeds.
Deleting WoonLens data never deletes the external identity-provider account.

The local account foundation encrypts Redis login and token state with
AES-256-GCM and hashes opaque browser handles before using them as Redis keys.
The checked-in Compose passwords and encryption key are synthetic development
fixtures. Production configuration rejects the fixture encryption key and
requires HTTPS front-channel OIDC URLs. FastAPI authentication failures return
a generic problem response with a `WWW-Authenticate: Bearer` challenge and do
not disclose token-validation details.

## Supported versions

There are no supported releases yet. This section will be updated when the
first tagged version is published.
