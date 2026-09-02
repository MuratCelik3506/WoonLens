import { getAccountServerConfig } from "@/lib/config/server-env";

export type FavouriteReference = Readonly<{
  id: string;
  pdok_address_id: string;
  created_at: string;
}>;

export async function requestBackendFavourites(
  accessToken: string,
): Promise<Readonly<{ items: readonly FavouriteReference[] }>> {
  return request("/api/v1/favourites", accessToken);
}

export async function createBackendFavourite(
  accessToken: string,
  pdokAddressId: string,
): Promise<FavouriteReference> {
  return request("/api/v1/favourites", accessToken, {
    body: JSON.stringify({ pdok_address_id: pdokAddressId }),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
}

export async function deleteBackendFavourite(
  accessToken: string,
  favouriteId: string,
): Promise<void> {
  await request(`/api/v1/favourites/${favouriteId}`, accessToken, {
    method: "DELETE",
  });
}

export async function resolveBackendFavourite(
  accessToken: string,
  favouriteId: string,
): Promise<unknown> {
  return request(`/api/v1/favourites/${favouriteId}/address`, accessToken);
}

async function request<T>(
  path: string,
  accessToken: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(new URL(path, getAccountServerConfig().apiBaseUrl), {
    ...init,
    cache: "no-store",
    headers: { Authorization: `Bearer ${accessToken}`, ...init.headers },
  });
  if (!response.ok) throw new Error(`favourite request failed (${response.status})`);
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}
