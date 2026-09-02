import { NextResponse } from "next/server";

import { exportBackendAccountData } from "@/features/account/server/backend-account";
import { accessToken } from "@/features/favourites/server/authenticated-session";

export async function GET(): Promise<Response> {
  const token = await accessToken();
  if (!token)
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  try {
    const data = await exportBackendAccountData(token);
    return new Response(JSON.stringify(data, null, 2), {
      headers: {
        "Cache-Control": "no-store",
        "Content-Disposition": 'attachment; filename="woonlens-account-data.json"',
        "Content-Type": "application/json; charset=utf-8",
      },
    });
  } catch {
    return NextResponse.json({ error: "account export unavailable" }, { status: 502 });
  }
}
