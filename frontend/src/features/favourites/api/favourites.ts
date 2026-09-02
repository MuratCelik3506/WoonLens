import type { AddressSuggestion } from "@/features/address-search/model/address-suggestion";

export type Favourite = Readonly<{
  id: string;
  pdokAddressId: string;
  createdAt: string;
}>;

export async function listFavourites(): Promise<readonly Favourite[]> {
  const response = await fetch("/api/favourites", { cache: "no-store" });
  if (!response.ok) throw new Error(`favourites unavailable (${response.status})`);
  const value = (await response.json()) as {
    items?: { id?: unknown; pdok_address_id?: unknown; created_at?: unknown }[];
  };
  if (!Array.isArray(value.items)) throw new Error("invalid favourites response");
  return value.items.map((item) => {
    if (
      typeof item.id !== "string" ||
      typeof item.pdok_address_id !== "string" ||
      typeof item.created_at !== "string"
    )
      throw new Error("invalid favourite response");
    return {
      id: item.id,
      pdokAddressId: item.pdok_address_id,
      createdAt: item.created_at,
    };
  });
}

export async function saveFavourite(pdokAddressId: string): Promise<Favourite> {
  const response = await fetch("/api/favourites", {
    body: JSON.stringify({ pdok_address_id: pdokAddressId }),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
  if (!response.ok)
    throw new Error(`favourite could not be saved (${response.status})`);
  return parseFavourite(await response.json());
}

export async function removeFavourite(id: string): Promise<void> {
  const response = await fetch(`/api/favourites/${id}`, { method: "DELETE" });
  if (!response.ok)
    throw new Error(`favourite could not be removed (${response.status})`);
}

export async function resolveFavourite(id: string): Promise<AddressSuggestion> {
  const response = await fetch(`/api/favourites/${id}/address`, { cache: "no-store" });
  if (!response.ok)
    throw new Error(`favourite could not be resolved (${response.status})`);
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
    throw new Error("invalid resolved favourite response");
  const addition = [value.house_letter, value.house_number_suffix]
    .filter((part): part is string => typeof part === "string" && part.length > 0)
    .join("-");
  return {
    id: value.id,
    displayName: `${value.street} ${value.house_number}${addition ? ` ${addition}` : ""}, ${value.postal_code} ${value.city}`,
    source: { provider: source.provider, dataset: source.dataset },
  };
}

function parseFavourite(value: unknown): Favourite {
  if (
    typeof value !== "object" ||
    value === null ||
    typeof (value as Record<string, unknown>).id !== "string" ||
    typeof (value as Record<string, unknown>).pdok_address_id !== "string" ||
    typeof (value as Record<string, unknown>).created_at !== "string"
  ) {
    throw new Error("invalid favourite response");
  }
  const item = value as Record<string, string>;
  return {
    id: item.id,
    pdokAddressId: item.pdok_address_id,
    createdAt: item.created_at,
  };
}
