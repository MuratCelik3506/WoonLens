import { NextResponse } from "next/server";

import {
  AddressSearchError,
  requestAddressSuggestions,
} from "@/features/address-search/api/address-suggestions";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const query = new URL(request.url).searchParams.get("q")?.trim() ?? "";
  if (query.length < 2 || query.length > 200) {
    return NextResponse.json(
      { title: "Enter between 2 and 200 characters" },
      { status: 422 },
    );
  }

  try {
    const suggestions = await requestAddressSuggestions(
      query,
      fetch,
      undefined,
      request.signal,
    );
    return NextResponse.json(
      {
        items: suggestions.items.map((item) => ({
          display_name: item.displayName,
          id: item.id,
          source: item.source,
        })),
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    const status = error instanceof AddressSearchError ? error.status : 502;
    return NextResponse.json(
      { title: "Address search is currently unavailable" },
      { headers: { "Cache-Control": "no-store" }, status },
    );
  }
}
