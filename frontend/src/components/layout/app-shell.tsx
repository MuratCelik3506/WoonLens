import type { ReactNode } from "react";

type AppShellProps = Readonly<{
  accountAccess?: ReactNode;
  comparisonExperience?: ReactNode;
  systemStatus?: ReactNode;
}>;

const navigation = [
  ["Compare", "#compare"],
  ["How it works", "#how-it-works"],
  ["Data sources", "#data-sources"],
  ["Privacy", "#privacy"],
  ["About", "#about"],
] as const;

export function AppShell({
  accountAccess,
  comparisonExperience,
  systemStatus,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-page text-ink">
      <a
        className="sr-only z-50 rounded-md bg-surface px-4 py-3 focus:not-sr-only focus:absolute focus:left-4 focus:top-4"
        href="#main-content"
      >
        Skip to main content
      </a>

      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex min-h-18 max-w-7xl items-center justify-between gap-6 px-5 py-3 lg:px-8">
          <a
            aria-label="WoonLens home"
            className="text-xl font-semibold tracking-tight no-underline"
            href="#compare"
          >
            Woon<span className="text-accent">Lens</span>
          </a>

          <nav aria-label="Primary" className="hidden md:block">
            <ul className="flex items-center gap-6 text-sm font-medium">
              {navigation.map(([label, href]) => (
                <li key={href}>
                  <a className="no-underline hover:text-accent" href={href}>
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div className="flex items-center gap-2">
            {accountAccess}
            <a
              className="hidden min-h-11 items-center rounded-lg border border-border px-4 text-sm font-medium no-underline hover:bg-accent-soft sm:inline-flex"
              href="https://github.com/MuratCelik3506/WoonLens"
              rel="noreferrer"
              target="_blank"
            >
              GitHub
              <span className="sr-only"> (opens in a new tab)</span>
            </a>
          </div>
        </div>
      </header>

      <main id="main-content">
        {comparisonExperience ?? <ComparisonFoundation />}

        <section className="border-y border-border bg-surface" id="how-it-works">
          <div className="mx-auto grid max-w-7xl gap-8 px-5 py-12 md:grid-cols-3 lg:px-8">
            <FoundationPoint
              description="BAG, EP-Online, CBS, and RIVM remain identifiable at the point of use."
              title="Official sources"
            />
            <FoundationPoint
              description="The complete comparison flow is available without registration."
              title="No account required"
            />
            <FoundationPoint
              description="Provider facts are requested live and are not retained by WoonLens."
              title="Live, not stored"
            />
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 py-12 lg:px-8" id="data-sources">
          <h2 className="text-2xl font-semibold tracking-tight">
            Built for explainable comparison
          </h2>
          <p className="mt-4 max-w-3xl leading-7 text-muted">
            Every future result will distinguish property records, neighbourhood
            context, and monitoring-station observations. Missing data will never be
            treated as a verdict about a home.
          </p>
          <div className="mt-8">{systemStatus}</div>
        </section>
      </main>

      <footer className="border-t border-border bg-surface" id="privacy">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <p id="about">WoonLens is an open-source, privacy-first research tool.</p>
          <p>No ranking. No provider-data retention.</p>
        </div>
      </footer>
    </div>
  );
}

function ComparisonFoundation() {
  return (
    <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28" id="compare">
      <p className="mb-5 text-sm font-semibold uppercase tracking-[0.16em] text-accent">
        Official data. Clear differences.
      </p>
      <h1 className="max-w-3xl text-4xl font-semibold tracking-[-0.04em] sm:text-5xl lg:text-6xl">
        Compare Dutch homes with trusted public data.
      </h1>
    </section>
  );
}

function FoundationPoint({
  description,
  title,
}: Readonly<{ description: string; title: string }>) {
  return (
    <article>
      <h2 className="text-base font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted">{description}</p>
    </article>
  );
}
