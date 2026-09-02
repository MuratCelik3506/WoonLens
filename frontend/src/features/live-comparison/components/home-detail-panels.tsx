import type {
  HomeDetailFact,
  LiveComparison,
} from "@/features/live-comparison/model/live-comparison";

function formatFact(fact: HomeDetailFact): string {
  if (fact.value === null) return "Not reported by the source";
  if (Array.isArray(fact.value))
    return fact.value.length > 0 ? fact.value.join(", ") : "Not reported by the source";
  const value =
    typeof fact.value === "number"
      ? new Intl.NumberFormat("en-NL", { maximumFractionDigits: 2 }).format(fact.value)
      : typeof fact.value === "string"
        ? fact.value
        : fact.value.join(", ");
  return fact.unit ? `${value} ${fact.unit}` : value;
}

function isTechnical(fact: HomeDetailFact): boolean {
  return /\b(ID|code)\b/i.test(fact.label);
}

function FactList({ facts }: Readonly<{ facts: readonly HomeDetailFact[] }>) {
  return (
    <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
      {facts.map((fact) => (
        <div className="border-t border-border pt-3" key={fact.label}>
          <dt className="text-xs font-semibold text-muted">{fact.label}</dt>
          <dd className="mt-1 break-words text-sm">{formatFact(fact)}</dd>
        </div>
      ))}
    </dl>
  );
}

export function HomeDetailPanels({
  comparison,
  labels,
}: Readonly<{
  comparison: LiveComparison;
  labels: ReadonlyMap<string, string>;
}>) {
  return (
    <section
      aria-labelledby="home-details-title"
      className="mt-8 scroll-mt-6"
      id="home-details"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
        One coherent live snapshot
      </p>
      <h3 className="mt-2 text-2xl font-semibold" id="home-details-title">
        Official details by home
      </h3>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
        Open a home to inspect the official records already used for this comparison.
        Opening a panel does not request or store additional provider data.
      </p>

      <div className="mt-5 space-y-4">
        {comparison.homes.map((home, index) => (
          <details
            className="rounded-xl border border-border bg-surface"
            key={home.addressId}
          >
            <summary className="min-h-14 cursor-pointer px-5 py-5 font-semibold sm:px-6">
              Home {index + 1} ·{" "}
              {labels.get(home.addressId) ?? home.displayName ?? "Unavailable home"}
            </summary>
            <div className="border-t border-border px-5 py-6 sm:px-6">
              {home.details.length === 0 ? (
                <p className="text-sm text-muted">
                  Official detail sections are unavailable for this home.
                </p>
              ) : (
                <div className="grid gap-5 xl:grid-cols-2">
                  {home.details.map((section) => {
                    const facts = section.facts.filter((fact) => !isTechnical(fact));
                    const technical = section.facts.filter(isTechnical);
                    return (
                      <article
                        className="rounded-lg border border-border p-5"
                        key={`${section.level}:${section.title}`}
                      >
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-accent">
                          {section.level} level
                        </p>
                        <h4 className="mt-1 text-lg font-semibold">{section.title}</h4>
                        <div className="mt-4">
                          <FactList facts={facts} />
                        </div>
                        {section.limitation ? (
                          <p className="mt-4 text-xs leading-5 text-muted">
                            {section.limitation}
                          </p>
                        ) : null}
                        {technical.length > 0 ? (
                          <details className="mt-4 border-t border-border pt-2">
                            <summary className="min-h-11 cursor-pointer py-3 text-sm font-semibold">
                              Technical identifiers
                            </summary>
                            <FactList facts={technical} />
                          </details>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
