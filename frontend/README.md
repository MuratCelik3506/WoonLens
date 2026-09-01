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
