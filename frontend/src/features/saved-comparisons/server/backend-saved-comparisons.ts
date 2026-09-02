import { getAccountServerConfig } from "@/lib/config/server-env";

export async function backendSavedComparisons(
  accessToken: string,
  path = "",
  init: RequestInit = {},
): Promise<Response> {
  return fetch(
    new URL(`/api/v1/saved-comparisons${path}`, getAccountServerConfig().apiBaseUrl),
    {
      ...init,
      cache: "no-store",
      headers: { Authorization: `Bearer ${accessToken}`, ...init.headers },
    },
  );
}
