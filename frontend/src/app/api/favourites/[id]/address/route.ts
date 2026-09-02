import { NextResponse } from "next/server";

import { accessToken } from "@/features/favourites/server/authenticated-session";
import { resolveBackendFavourite } from "@/features/favourites/server/backend-favourites";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
): Promise<Response> {
  const token = await accessToken();
  if (!token)
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  try {
    return NextResponse.json(
      await resolveBackendFavourite(token, (await context.params).id),
      {
        headers: { "Cache-Control": "no-store" },
      },
    );
  } catch {
    return NextResponse.json({ error: "favourite unavailable" }, { status: 404 });
  }
}
