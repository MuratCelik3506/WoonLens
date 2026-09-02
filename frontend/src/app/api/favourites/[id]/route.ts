import { NextResponse } from "next/server";

import { requireSameOrigin } from "@/features/account/server/request-security";
import { accessToken } from "@/features/favourites/server/authenticated-session";
import { deleteBackendFavourite } from "@/features/favourites/server/backend-favourites";
import { getAccountServerConfig } from "@/lib/config/server-env";

export async function DELETE(
  request: Request,
  context: { params: Promise<{ id: string }> },
): Promise<Response> {
  try {
    requireSameOrigin(request, getAccountServerConfig().oidcRedirectUri.origin);
    const token = await accessToken();
    if (!token)
      return NextResponse.json({ error: "authentication required" }, { status: 401 });
    await deleteBackendFavourite(token, (await context.params).id);
    return new Response(null, {
      status: 204,
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json({ error: "request rejected" }, { status: 403 });
  }
}
