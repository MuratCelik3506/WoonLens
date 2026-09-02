import { NextResponse } from "next/server";

import { getServerConfig } from "@/lib/config/server-env";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const url = new URL("/api/v1/addresses/resolve", getServerConfig().apiBaseUrl);
  url.searchParams.set("id", (await context.params).id);
  const response = await fetch(url, { cache: "no-store" });
  return new NextResponse(response.body, {
    status: response.status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
