import { NextResponse } from "next/server";

import {
  LiveComparisonError,
  requestLiveComparison,
  validateAddressIds,
} from "@/features/live-comparison/api/live-comparison";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const payload: unknown = await request.json();
    if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
      throw new LiveComparisonError("Invalid comparison request", 422);
    }
    const addressIds = validateAddressIds(
      (payload as Record<string, unknown>).address_ids,
    );
    const comparison = await requestLiveComparison(
      addressIds,
      fetch,
      undefined,
      request.signal,
    );
    return NextResponse.json(comparison, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    const status = error instanceof LiveComparisonError ? error.status : 422;
    const title =
      status === 422
        ? "Select between two and five unique official addresses"
        : "Live comparison is currently unavailable";
    return NextResponse.json(
      { title },
      { headers: { "Cache-Control": "no-store" }, status },
    );
  }
}
