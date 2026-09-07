# Changelog

All notable changes to WoonLens are documented in this file.

The project follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-08

### Added

- Live comparison of two to five Dutch homes using official PDOK, BAG,
  EP-Online, CBS, and Luchtmeetnet/RIVM sources.
- Source-level provenance, retrieval times, missing-data explanations, neutral
  insights, and cross-register audit rules without a universal score.
- Request-scoped property, energy, neighbourhood, air-quality, and map context.
- Non-retained JSON and PDF evidence downloads.
- A responsive, accessible guest-first Next.js interface with deterministic
  browser coverage.
- Optional OIDC accounts with encrypted Redis-backed browser sessions.
- Minimum owner-scoped favourites and named saved-comparison recipes that rerun
  the live provider pipeline.
- Privacy-minimal account export and transactional account deletion.
- Docker Compose development runtime with FastAPI, Next.js, PostgreSQL, Redis,
  Alembic, and a synthetic Keycloak realm.
- Automated formatting, linting, strict typing, architecture checks, unit tests,
  coverage enforcement, production frontend build, and Chromium smoke tests.

### Security and privacy

- Provider responses, normalized property facts, comparison results, generated
  reports, address labels, and automatic search history are not persisted.
- Browser JavaScript never receives OIDC provider tokens.
- Account operations are authenticated and owner-scoped; destructive BFF
  requests require exact same-origin validation.
- Repository examples and Docker credentials are synthetic development fixtures.

### Known limitations

- Version 1.0.0 is a local Docker release, not a hosted production service.
- EP-Online energy data requires a personal server-side API key.
- Upstream source availability and field coverage vary by address.
- No price prediction, mortgage advice, property ranking, historical timeline,
  scraping, or user file upload is provided.
- Production hosting, OIDC selection, backup operations, monitoring, and SLA are
  intentionally deployment-specific and are not included in this release.

[1.0.0]: https://github.com/MuratCelik3506/WoonLens/releases/tag/v1.0.0
