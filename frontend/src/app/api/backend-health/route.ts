import { NextResponse } from "next/server";

import { getHealthStatus } from "@/features/system-status/api/health";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(await getHealthStatus(), {
    headers: { "Cache-Control": "no-store" },
  });
}
