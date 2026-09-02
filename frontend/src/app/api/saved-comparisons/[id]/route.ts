import { NextResponse } from "next/server";

import { requireSameOrigin } from "@/features/account/server/request-security";
import { accessToken } from "@/features/favourites/server/authenticated-session";
import { backendSavedComparisons } from "@/features/saved-comparisons/server/backend-saved-comparisons";
import { getAccountServerConfig } from "@/lib/config/server-env";

async function mutate(request: Request, id: string, method: "PATCH" | "DELETE") {
  try {
    requireSameOrigin(request, getAccountServerConfig().oidcRedirectUri.origin);
  } catch {
    return NextResponse.json({ error: "request rejected" }, { status: 403 });
  }
  const token = await accessToken();
  if (!token)
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  const response = await backendSavedComparisons(token, `/${id}`, {
    body: method === "PATCH" ? await request.text() : undefined,
    headers: method === "PATCH" ? { "Content-Type": "application/json" } : undefined,
    method,
  });
  return new Response(response.body, {
    status: response.status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

export async function PATCH(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return mutate(request, (await context.params).id, "PATCH");
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return mutate(request, (await context.params).id, "DELETE");
}
