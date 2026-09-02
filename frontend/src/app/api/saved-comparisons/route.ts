import { NextResponse } from "next/server";

import { requireSameOrigin } from "@/features/account/server/request-security";
import { accessToken } from "@/features/favourites/server/authenticated-session";
import { backendSavedComparisons } from "@/features/saved-comparisons/server/backend-saved-comparisons";
import { getAccountServerConfig } from "@/lib/config/server-env";

export async function GET(): Promise<Response> {
  const token = await accessToken();
  if (!token)
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  const response = await backendSavedComparisons(token);
  return new Response(response.body, {
    status: response.status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

export async function POST(request: Request): Promise<Response> {
  try {
    requireSameOrigin(request, getAccountServerConfig().oidcRedirectUri.origin);
  } catch {
    return NextResponse.json({ error: "request rejected" }, { status: 403 });
  }
  const token = await accessToken();
  if (!token)
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  const response = await backendSavedComparisons(token, "", {
    body: await request.text(),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
  return new Response(response.body, {
    status: response.status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
