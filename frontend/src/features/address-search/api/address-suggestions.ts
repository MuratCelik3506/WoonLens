import {
  parseAddressSuggestions,
  type AddressSuggestions,
} from "@/features/address-search/model/address-suggestion";
import { getServerConfig } from "@/lib/config/server-env";

export class AddressSearchError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export async function requestAddressSuggestions(
  query: string,
  fetcher: typeof fetch = fetch,
  apiBaseUrl: URL = getServerConfig().apiBaseUrl,
  signal?: AbortSignal,
): Promise<AddressSuggestions> {
  const url = new URL("/api/v1/addresses/suggest", apiBaseUrl);
  url.searchParams.set("q", query);

  const response = await fetcher(url, { cache: "no-store", signal });
  if (!response.ok) {
    throw new AddressSearchError(
      "Address search is currently unavailable",
      response.status,
    );
  }

  return parseAddressSuggestions(await response.json());
}

export async function searchAddresses(
  query: string,
  signal?: AbortSignal,
): Promise<AddressSuggestions> {
  const url = new URL("/api/addresses/suggest", window.location.origin);
  url.searchParams.set("q", query);

  const response = await fetch(url, { cache: "no-store", signal });
  if (!response.ok) {
    throw new AddressSearchError(
      "Address search is currently unavailable",
      response.status,
    );
  }

  return parseAddressSuggestions(await response.json());
}
