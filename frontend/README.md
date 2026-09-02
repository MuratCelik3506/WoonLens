# WoonLens Frontend

The WoonLens web interface is a Next.js App Router application written in
TypeScript. It consumes the public FastAPI contract and must preserve the
guest-first, neutral, source-backed, and transient-data rules in
[`../docs/UI_UX_SPECIFICATION.md`](../docs/UI_UX_SPECIFICATION.md).

## Local Development

Docker Compose is the canonical full-stack runtime:

```bash
docker compose up --build api frontend
```

Open `http://localhost:3000`. The frontend health proxy reaches the API through
the internal Docker service name; browser-visible configuration never contains
provider credentials.

The optional account button starts a local Keycloak Authorization Code + PKCE
flow. The callback provisions the minimum FastAPI account and keeps provider
tokens in an expiring, AES-256-GCM-encrypted Redis session. Browser JavaScript
can query only `/api/auth/session`; it never receives an access, refresh, or ID
token. Local login uses the synthetic `woonlens-demo` /
`local-development-only` fixture and is not a production identity setup.
Deployments that do not set `WOONLENS_ACCOUNT_FEATURES_ENABLED=true` hide the
account control while preserving the complete guest comparison journey.

For frontend-only development:

```bash
cd frontend
npm ci
npm run dev
```

## Quality Checks

```bash
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:e2e
```

The Docker tools profile runs the non-browser frontend quality chain in a clean
container:

```bash
docker compose run --rm frontend-check
```

Playwright requires Chromium once per development machine:

```bash
npx playwright install chromium
```

## Boundaries

- Provider-specific response interpretation belongs to backend adapters.
- Public browser variables use the `NEXT_PUBLIC_` prefix and must contain no
  credentials.
- The Next.js server uses `WOONLENS_API_BASE_URL` for internal API calls.
- TanStack Query defaults discard inactive query data immediately; future
  features must not turn client caching into provider-data persistence.
- Guest comparison must remain complete without authentication.
- UI text must not rank, score, or recommend homes.
