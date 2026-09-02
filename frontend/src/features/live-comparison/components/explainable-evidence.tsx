import type { LiveComparison } from "@/features/live-comparison/model/live-comparison";

function humanize(value: string): string {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replaceAll(".", " · ")
    .replace(/^./, (letter) => letter.toUpperCase());
}

function auditValue(value: number | string | null): string {
  if (value === null) return "Not available from the source";
  return typeof value === "number"
    ? new Intl.NumberFormat("en-NL", { maximumFractionDigits: 2 }).format(value)
    : value;
}

export function ExplainableEvidence({
  comparison,
  labels,
}: Readonly<{
  comparison: LiveComparison;
  labels: ReadonlyMap<string, string>;
}>) {
  const homeNumber = new Map(
    comparison.homes.map((home, index) => [home.addressId, `Home ${index + 1}`]),
  );

  return (
    <div
      className="mt-8 grid scroll-mt-6 gap-8 xl:grid-cols-2"
      id="explainable-evidence"
    >
      <section
        aria-labelledby="explainable-differences-title"
        className="rounded-xl border border-border bg-surface p-6"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
          Deterministic rules · version {comparison.rulesVersion}
        </p>
        <h3 className="mt-2 text-xl font-semibold" id="explainable-differences-title">
          Explainable differences
        </h3>
        <p className="mt-2 text-sm leading-6 text-muted">
          Backend-owned rules describe reported facts and limitations. They do not
          score, rank, or recommend a home.
        </p>

        {comparison.insights.length === 0 ? (
          <p className="mt-5 text-sm text-muted">No rule explanation was produced.</p>
        ) : (
          <ol className="mt-5 space-y-4">
            {comparison.insights.map((insight) => {
              const metric = comparison.metrics.find(
                (item) => item.key === insight.metricKey,
              );
              const homes = insight.addressIds.map(
                (addressId) => homeNumber.get(addressId) ?? "Selected home",
              );
              return (
                <li
                  className="rounded-lg border border-border p-4"
                  key={insight.ruleId}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h4 className="font-semibold">
                      {metric?.label ?? insight.metricKey}
                    </h4>
                    <span className="text-xs text-muted">
                      {humanize(insight.classification)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6">{insight.message}</p>
                  <p className="mt-2 text-xs text-muted">
                    {homes.length > 0
                      ? `Applies to ${homes.join(", ")}.`
                      : "No home has usable evidence for this rule."}
                  </p>
                  <details className="mt-3 border-t border-border pt-3 text-xs text-muted">
                    <summary className="min-h-11 cursor-pointer py-3 font-semibold text-ink">
                      Technical rule details
                    </summary>
                    <dl className="grid gap-2 pb-2 sm:grid-cols-[7rem_1fr]">
                      <dt>Rule ID</dt>
                      <dd className="break-all">{insight.ruleId}</dd>
                      <dt>Metric key</dt>
                      <dd className="break-all">{insight.metricKey}</dd>
                      <dt>Home references</dt>
                      <dd>{homes.length > 0 ? homes.join(", ") : "None"}</dd>
                    </dl>
                  </details>
                </li>
              );
            })}
          </ol>
        )}
      </section>

      <section
        aria-labelledby="cross-source-checks-title"
        className="rounded-xl border border-border bg-surface p-6"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
          Register definitions remain distinct
        </p>
        <h3 className="mt-2 text-xl font-semibold" id="cross-source-checks-title">
          Cross-source checks
        </h3>
        <p className="mt-2 text-sm leading-6 text-muted">
          These checks explain matches, missing evidence, and definition differences. A
          difference is not automatically a source error.
        </p>

        {comparison.audits.length === 0 ? (
          <p className="mt-5 text-sm text-muted">No cross-source check was produced.</p>
        ) : (
          <ol className="mt-5 space-y-4">
            {comparison.audits.map((audit) => {
              const number = homeNumber.get(audit.addressId) ?? "Selected home";
              return (
                <li
                  className="rounded-lg border border-border p-4"
                  key={`${audit.addressId}:${audit.ruleId}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h4 className="font-semibold">{number}</h4>
                    <span className="text-xs text-muted">
                      {humanize(audit.classification)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6">{audit.message}</p>
                  <p className="mt-2 text-xs text-muted">
                    {labels.get(audit.addressId) ?? "Official selected address"}
                  </p>
                  <details className="mt-3 border-t border-border pt-3 text-xs text-muted">
                    <summary className="min-h-11 cursor-pointer py-3 font-semibold text-ink">
                      Compared source fields
                    </summary>
                    <dl className="grid gap-2 pb-2 sm:grid-cols-[minmax(0,1fr)_minmax(8rem,auto)]">
                      {audit.fields.map((field, index) => (
                        <div className="contents" key={field}>
                          <dt className="break-all">{humanize(field)}</dt>
                          <dd>{auditValue(audit.values[index] ?? null)}</dd>
                        </div>
                      ))}
                      <dt>Rule ID</dt>
                      <dd className="break-all">{audit.ruleId}</dd>
                    </dl>
                  </details>
                </li>
              );
            })}
          </ol>
        )}
      </section>
    </div>
  );
}
