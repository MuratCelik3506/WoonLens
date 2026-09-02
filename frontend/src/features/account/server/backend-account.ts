import { getAccountServerConfig } from "@/lib/config/server-env";

export type CurrentAccount = Readonly<{
  id: string;
  created_at: string;
}>;

export async function ensureBackendAccount(
  accessToken: string,
): Promise<CurrentAccount> {
  return requestAccount("PUT", accessToken);
}

export async function fetchBackendAccount(
  accessToken: string,
): Promise<CurrentAccount> {
  return requestAccount("GET", accessToken);
}

export async function exportBackendAccountData(accessToken: string): Promise<unknown> {
  const url = new URL("/api/v1/account/export", getAccountServerConfig().apiBaseUrl);
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`account export failed (${response.status})`);
  return response.json();
}

export async function deleteBackendAccount(accessToken: string): Promise<void> {
  const url = new URL("/api/v1/account", getAccountServerConfig().apiBaseUrl);
  const response = await fetch(url, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`account deletion failed (${response.status})`);
}

async function requestAccount(
  method: "GET" | "PUT",
  accessToken: string,
): Promise<CurrentAccount> {
  const url = new URL("/api/v1/account", getAccountServerConfig().apiBaseUrl);
  const response = await fetch(url, {
    method,
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`authenticated account request failed (${response.status})`);
  }
  return (await response.json()) as CurrentAccount;
}
