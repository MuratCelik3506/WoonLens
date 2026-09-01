import { getServerConfig } from "@/lib/config/server-env";

export type HealthStatus = Readonly<{
  available: boolean;
  status: "ok" | "unavailable";
}>;

type HealthPayload = Readonly<{
  status: unknown;
}>;

export async function getHealthStatus(
  fetcher: typeof fetch = fetch,
  apiBaseUrl: URL = getServerConfig().apiBaseUrl,
): Promise<HealthStatus> {
  try {
    const response = await fetcher(new URL("/api/v1/health", apiBaseUrl), {
      cache: "no-store",
      signal: AbortSignal.timeout(2_500),
    });

    if (!response.ok) {
      return { available: false, status: "unavailable" };
    }

    const payload = (await response.json()) as HealthPayload;
    if (payload.status !== "ok") {
      return { available: false, status: "unavailable" };
    }

    return { available: true, status: "ok" };
  } catch {
    return { available: false, status: "unavailable" };
  }
}
