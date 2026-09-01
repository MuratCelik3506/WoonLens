"use client";

import { useMutation } from "@tanstack/react-query";

import {
  downloadComparison,
  type ComparisonDownloadFormat,
} from "@/features/comparison-downloads/api/comparison-download";

function saveDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.hidden = true;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function DownloadActions({
  addressIds,
}: Readonly<{ addressIds: readonly string[] }>) {
  const report = useMutation({
    mutationFn: (format: ComparisonDownloadFormat) =>
      downloadComparison(format, addressIds),
    onSuccess: ({ blob, filename }) => saveDownload(blob, filename),
  });
  const activeFormat = report.variables;

  return (
    <div className="mt-6 rounded-xl border border-border bg-surface p-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="font-semibold">Download this evidence snapshot</h3>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-muted">
            Each file reruns live sources and includes generation time, attribution,
            warnings, and limitations. WoonLens does not retain the generated file.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {(["json", "pdf"] as const).map((format) => (
            <button
              className="min-h-11 rounded-lg border border-border px-4 text-sm font-semibold hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-60"
              disabled={report.isPending}
              key={format}
              onClick={() => report.mutate(format)}
              type="button"
            >
              {report.isPending && activeFormat === format
                ? `Generating ${format.toUpperCase()}…`
                : `Download ${format.toUpperCase()}`}
            </button>
          ))}
        </div>
      </div>
      <p aria-live="polite" className="mt-3 min-h-5 text-xs text-muted" role="status">
        {report.isError
          ? "The report could not be generated. Your comparison is unchanged; try again."
          : report.isSuccess
            ? `${activeFormat?.toUpperCase()} download started.`
            : report.isPending
              ? `Requesting a fresh ${activeFormat?.toUpperCase()} report.`
              : "Choose JSON for structured data or PDF for a readable evidence report."}
      </p>
    </div>
  );
}
