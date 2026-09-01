import {
  isUuid,
  parseLiveComparison,
  type LiveComparison,
} from "@/features/live-comparison/model/live-comparison";
import { getServerConfig } from "@/lib/config/server-env";

export class LiveComparisonError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export function validateAddressIds(value: unknown): readonly string[] {
  if (!Array.isArray(value) || value.length < 2 || value.length > 5) {
    throw new LiveComparisonError("Select between two and five homes", 422);
  }
  if (!value.every(isUuid) || new Set(value).size !== value.length) {
    throw new LiveComparisonError("Select unique official addresses", 422);
  }
  return value;
}

export async function requestLiveComparison(
  addressIds: readonly string[],
  fetcher: typeof fetch = fetch,
  apiBaseUrl: URL = getServerConfig().apiBaseUrl,
  signal?: AbortSignal,
): Promise<LiveComparison> {
  const ids = validateAddressIds(addressIds);
  const response = await fetcher(new URL("/api/v1/comparisons/live", apiBaseUrl), {
    body: JSON.stringify({ address_ids: ids }),
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    method: "POST",
    signal,
  });
  if (!response.ok) {
    throw new LiveComparisonError(
      "Live comparison is currently unavailable",
      response.status,
    );
  }
  try {
    return parseLiveComparison(await response.json());
  } catch {
    throw new LiveComparisonError("The comparison response could not be verified", 502);
  }
}

export async function compareHomes(
  addressIds: readonly string[],
  signal?: AbortSignal,
): Promise<LiveComparison> {
  const response = await fetch("/api/comparisons/live", {
    body: JSON.stringify({ address_ids: validateAddressIds(addressIds) }),
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    method: "POST",
    signal,
  });
  if (!response.ok) {
    throw new LiveComparisonError(
      "Live comparison is currently unavailable",
      response.status,
    );
  }
  try {
    return parseLiveComparison(await response.json());
  } catch {
    throw new LiveComparisonError("The comparison response could not be verified", 502);
  }
}
