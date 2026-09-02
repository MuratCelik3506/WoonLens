import { NextResponse } from "next/server";

import {
  createBackendFavourite,
  requestBackendFavourites,
} from "@/features/favourites/server/backend-favourites";
import { accessToken } from "@/features/favourites/server/authenticated-session";
import { requireSameOrigin } from "@/features/account/server/request-security";
import { getAccountServerConfig } from "@/lib/config/server-env";

export async function GET(): Promise<Response> {
  const token = await accessToken();
  if (!token)
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  try {
    return NextResponse.json(await requestBackendFavourites(token), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json({ error: "favourites unavailable" }, { status: 502 });
  }
}

export async function POST(request: Request): Promise<Response> {
  try {
    requireSameOrigin(request, getAccountServerConfig().oidcRedirectUri.origin);
    const token = await accessToken();
    if (!token)
      return NextResponse.json({ error: "authentication required" }, { status: 401 });
    const body = (await request.json()) as { pdok_address_id?: unknown };
    if (typeof body.pdok_address_id !== "string" || Object.keys(body).length !== 1) {
      return NextResponse.json({ error: "invalid favourite" }, { status: 422 });
    }
    return NextResponse.json(await createBackendFavourite(token, body.pdok_address_id));
  } catch {
    return NextResponse.json({ error: "request rejected" }, { status: 403 });
  }
}
