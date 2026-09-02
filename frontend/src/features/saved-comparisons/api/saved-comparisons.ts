import type { AddressSuggestion } from "@/features/address-search/model/address-suggestion";

export type SavedComparison = Readonly<{
  id: string;
  name: string;
  addressIds: readonly string[];
}>;

export async function listSavedComparisons(): Promise<readonly SavedComparison[]> {
  const response = await fetch("/api/saved-comparisons", { cache: "no-store" });
  if (!response.ok) throw new Error("saved comparisons unavailable");
  const value = (await response.json()) as { items?: unknown[] };
  if (!Array.isArray(value.items)) throw new Error("invalid saved comparisons");
  return value.items.map(parseSavedComparison);
}

export async function createSavedComparison(
  input: Readonly<{ name: string; addressIds: readonly string[] }>,
): Promise<SavedComparison> {
  return mutate("/api/saved-comparisons", "POST", {
    name: input.name,
    address_ids: input.addressIds,
  });
}

export async function renameSavedComparison(
  input: Readonly<{ id: string; name: string }>,
): Promise<SavedComparison> {
  return mutate(`/api/saved-comparisons/${input.id}`, "PATCH", { name: input.name });
}

export async function deleteSavedComparison(id: string): Promise<string> {
  const response = await fetch(`/api/saved-comparisons/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error("saved comparison could not be deleted");
  return id;
}

export async function resolveSavedAddresses(
  addressIds: readonly string[],
): Promise<readonly AddressSuggestion[]> {
  return Promise.all(
    addressIds.map(async (id) => {
      const response = await fetch(`/api/addresses/${id}`, { cache: "no-store" });
      if (!response.ok) throw new Error("a saved address is unavailable");
      const value = (await response.json()) as Record<string, unknown>;
      const source = value.source as Record<string, unknown> | undefined;
      if (
        typeof value.id !== "string" ||
        typeof value.street !== "string" ||
        typeof value.house_number !== "string" ||
        typeof value.postal_code !== "string" ||
        typeof value.city !== "string" ||
        typeof source?.provider !== "string" ||
        typeof source.dataset !== "string"
      )
        throw new Error("invalid saved address");
      return {
        id: value.id,
        displayName: `${value.street} ${value.house_number}, ${value.postal_code} ${value.city}`,
        source: { provider: source.provider, dataset: source.dataset },
      };
    }),
  );
}

async function mutate(path: string, method: "POST" | "PATCH", body: unknown) {
  const response = await fetch(path, {
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
    method,
  });
  if (!response.ok) throw new Error("saved comparison mutation failed");
  return parseSavedComparison(await response.json());
}

function parseSavedComparison(value: unknown): SavedComparison {
  const item = value as Record<string, unknown>;
  if (
    !item ||
    typeof item.id !== "string" ||
    typeof item.name !== "string" ||
    !Array.isArray(item.address_ids) ||
    !item.address_ids.every((id) => typeof id === "string")
  )
    throw new Error("invalid saved comparison");
  return { id: item.id, name: item.name, addressIds: item.address_ids };
}
