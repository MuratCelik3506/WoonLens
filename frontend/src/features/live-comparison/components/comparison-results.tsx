import type {
  ComparedMetric,
  LiveComparison,
} from "@/features/live-comparison/model/live-comparison";
import { DownloadActions } from "@/features/comparison-downloads/components/download-actions";
import { ExplainableEvidence } from "@/features/live-comparison/components/explainable-evidence";
import { HomeDetailPanels } from "@/features/live-comparison/components/home-detail-panels";
import { SpatialContext } from "@/features/map/components/spatial-context";

const sections = [
  {
    description: "Official BAG property and building records.",
    keys: ["registered_area_m2", "construction_year"],
    title: "Property",
  },
  {
    description: "Current registration fields supplied by EP-Online.",
    keys: [
      "energy_class",
      "thermal_zone_area_m2",
      "energy_demand_kwh_m2_year",
      "primary_fossil_energy_kwh_m2_year",
      "renewable_energy_share_pct",
    ],
    title: "Energy registration",
  },
  {
    description: "CBS neighbourhood context, not a valuation of the selected home.",
    keys: ["average_woz_value"],
    title: "Neighbourhood context",
  },
  {
    description: "Recent nearby-station observations, not measurements at a home.",
    keys: ["air_quality_no2", "air_quality_pm10", "air_quality_pm2_5"],
    title: "Environmental station context",
  },
] as const;

function humanizeReason(reason: string): string {
  return reason.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function formatValue(metric: ComparedMetric, value: number | string): string {
  if (typeof value === "number") {
    const formatted = new Intl.NumberFormat("en-NL", {
      maximumFractionDigits: 2,
    }).format(value);
    return metric.unit === "EUR" ? `€${formatted}` : `${formatted} ${metric.unit}`;
  }
  return metric.unit === "class" || metric.unit === "year"
    ? value
    : `${value} ${metric.unit}`;
}

export function ComparisonResults({
  comparison,
  labels,
}: Readonly<{
  comparison: LiveComparison;
  labels: ReadonlyMap<string, string>;
}>) {
  const availableHomes = comparison.homes.filter(
    (home) => home.unavailableReason === null,
  );
  const isPartial = availableHomes.length !== comparison.homes.length;

  return (
    <section
      aria-labelledby="comparison-results-title"
      className="mx-auto max-w-7xl px-5 pb-24 lg:px-8"
    >
      <div className="border-t border-border pt-12">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-accent">
          Live official comparison
        </p>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2
              className="text-3xl font-semibold tracking-[-0.03em]"
              id="comparison-results-title"
            >
              Factual differences, source by source
            </h2>
            <p className="mt-3 max-w-3xl leading-7 text-muted">
              {isPartial
                ? availableHomes.length === 0
                  ? "No selected home returned a usable overview. Source-specific missing reasons remain visible below."
                  : "Some homes or sources were unavailable. Available facts remain visible below."
                : "The requested sources returned a comparison. No score or recommendation is applied."}
            </p>
          </div>
          <p className="text-sm text-muted">
            Rules {comparison.rulesVersion} · Requested live
          </p>
        </div>

        <nav aria-label="Comparison result sections" className="mt-8">
          <ul className="flex flex-wrap gap-2 text-sm">
            {[
              ["Comparison", "#comparison-tables"],
              ["Map", "#spatial-context"],
              ["Official details", "#home-details"],
              ["Explanations", "#explainable-evidence"],
              ["Sources and limits", "#sources-and-limits"],
              ["Selected homes", "#compare"],
            ].map(([label, href]) => (
              <li key={href}>
                <a
                  className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 font-semibold hover:bg-accent-soft"
                  href={href}
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        {comparison.homes.some((home) => home.unavailableReason !== null) ? (
          <div
            className="mt-8 rounded-xl border border-border bg-surface p-5"
            role="status"
          >
            <h3 className="font-semibold">Partially available comparison</h3>
            <ul className="mt-2 space-y-1 text-sm text-muted">
              {comparison.homes
                .filter((home) => home.unavailableReason !== null)
                .map((home) => (
                  <li key={home.addressId}>
                    {labels.get(home.addressId) ?? "Selected home"}:{" "}
                    {humanizeReason(home.unavailableReason ?? "unavailable")}
                  </li>
                ))}
            </ul>
          </div>
        ) : null}

        <DownloadActions addressIds={comparison.homes.map((home) => home.addressId)} />

        <div className="mt-10 scroll-mt-6 space-y-8" id="comparison-tables">
          {sections.map((section) => {
            const metrics = comparison.metrics.filter((metric) =>
              section.keys.includes(metric.key as never),
            );
            if (metrics.length === 0) return null;
            return (
              <article
                className="overflow-hidden rounded-xl border border-border bg-surface"
                key={section.title}
              >
                <div className="border-b border-border px-5 py-5 sm:px-6">
                  <h3 className="text-xl font-semibold">{section.title}</h3>
                  <p className="mt-1 text-sm text-muted">{section.description}</p>
                </div>
                <div
                  aria-label={`${section.title} comparison table; scroll horizontally for every selected home`}
                  className="overflow-x-auto"
                  role="region"
                  tabIndex={0}
                >
                  <table className="min-w-[44rem] w-full border-collapse text-left text-sm">
                    <thead>
                      <tr>
                        <th
                          className="w-64 px-5 py-4 font-semibold sm:px-6"
                          scope="col"
                        >
                          Fact
                        </th>
                        {comparison.homes.map((home, index) => (
                          <th
                            className="min-w-48 px-4 py-4 font-semibold"
                            key={home.addressId}
                            scope="col"
                          >
                            <span className="block text-xs text-accent">
                              Home {index + 1}
                            </span>
                            <span className="mt-1 block">
                              {labels.get(home.addressId) ??
                                home.displayName ??
                                "Unavailable home"}
                            </span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {metrics.map((metric) => (
                        <tr
                          className="border-t border-border align-top"
                          key={metric.key}
                        >
                          <th className="px-5 py-4 font-medium sm:px-6" scope="row">
                            {metric.label}
                            <span className="mt-1 block text-xs font-normal leading-5 text-muted">
                              {metric.definition}
                            </span>
                          </th>
                          {comparison.homes.map((home) => {
                            const item = metric.values.find(
                              (value) => value.addressId === home.addressId,
                            );
                            return (
                              <td className="px-4 py-4" key={home.addressId}>
                                {item?.value !== null && item?.value !== undefined ? (
                                  formatValue(metric, item.value)
                                ) : (
                                  <span className="text-muted">
                                    {humanizeReason(
                                      item?.missingReason ??
                                        home.unavailableReason ??
                                        "not available from source",
                                    )}
                                  </span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>
            );
          })}
        </div>

        <SpatialContext comparison={comparison} labels={labels} />

        <HomeDetailPanels comparison={comparison} labels={labels} />

        <ExplainableEvidence comparison={comparison} labels={labels} />

        <div
          className="mt-8 grid scroll-mt-6 gap-6 lg:grid-cols-2"
          id="sources-and-limits"
        >
          <article className="rounded-xl border border-border bg-surface p-6">
            <h3 className="text-lg font-semibold">Sources used</h3>
            <ul className="mt-4 space-y-4">
              {comparison.homes.map((home, index) => (
                <li key={home.addressId}>
                  <p className="text-sm font-semibold">Home {index + 1}</p>
                  {home.sources.length === 0 ? (
                    <p className="mt-1 text-sm text-muted">
                      No source response available.
                    </p>
                  ) : (
                    <ul className="mt-1 space-y-1 text-sm text-muted">
                      {home.sources.map((source) => (
                        <li
                          key={`${source.provider}:${source.dataset}:${source.retrievedAt}`}
                        >
                          {source.provider} · {source.dataset} · {source.license} ·
                          retrieved{" "}
                          {new Date(source.retrievedAt).toLocaleString("en-NL")}
                        </li>
                      ))}
                    </ul>
                  )}
                  {home.contextNotes.length > 0 ? (
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted">
                      {home.contextNotes.map((note) => (
                        <li key={note}>{note}</li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              ))}
            </ul>
          </article>
          <article className="rounded-xl border border-border bg-surface p-6">
            <h3 className="text-lg font-semibold">Interpretation limits</h3>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-muted">
              {comparison.notices.map((notice) => (
                <li key={notice.code}>{notice.message}</li>
              ))}
            </ul>
          </article>
        </div>
      </div>
    </section>
  );
}
