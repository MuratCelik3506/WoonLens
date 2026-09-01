import { validateAddressIds } from "@/features/live-comparison/api/live-comparison";
import { getServerConfig } from "@/lib/config/server-env";

export type ComparisonDownloadFormat = "json" | "pdf";

export type ComparisonDownload = Readonly<{
  blob: Blob;
  filename: string;
}>;

export class ComparisonDownloadError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const configuration = {
  json: { contentType: "application/json", extension: "json" },
  pdf: { contentType: "application/pdf", extension: "pdf" },
} as const;

function safeFilename(value: string | null, format: ComparisonDownloadFormat): string {
  const match = value?.match(
    new RegExp(`filename="(woonlens-comparison-[0-9]{8}T[0-9]{6}Z\\.${format})"`),
  );
  return match?.[1] ?? `woonlens-comparison.${format}`;
}

async function verifiedDownload(
  response: Response,
  format: ComparisonDownloadFormat,
): Promise<ComparisonDownload> {
  if (!response.ok) {
    throw new ComparisonDownloadError(
      `The ${format.toUpperCase()} report is currently unavailable`,
      response.status,
    );
  }
  const expected = configuration[format].contentType;
  if (!response.headers.get("Content-Type")?.startsWith(expected)) {
    throw new ComparisonDownloadError("The report format could not be verified", 502);
  }
  return {
    blob: await response.blob(),
    filename: safeFilename(response.headers.get("Content-Disposition"), format),
  };
}

export async function requestComparisonDownload(
  format: ComparisonDownloadFormat,
  addressIds: readonly string[],
  fetcher: typeof fetch = fetch,
  apiBaseUrl: URL = getServerConfig().apiBaseUrl,
  signal?: AbortSignal,
): Promise<ComparisonDownload> {
  const response = await fetcher(
    new URL(`/api/v1/comparison-downloads/${format}`, apiBaseUrl),
    {
      body: JSON.stringify({ address_ids: validateAddressIds(addressIds) }),
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      method: "POST",
      signal,
    },
  );
  return verifiedDownload(response, format);
}

export async function downloadComparison(
  format: ComparisonDownloadFormat,
  addressIds: readonly string[],
  signal?: AbortSignal,
): Promise<ComparisonDownload> {
  const response = await fetch(`/api/comparison-downloads/${format}`, {
    body: JSON.stringify({ address_ids: validateAddressIds(addressIds) }),
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    method: "POST",
    signal,
  });
  return verifiedDownload(response, format);
}
