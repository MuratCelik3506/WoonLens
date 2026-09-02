import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { sessionCookieName } from "@/features/account/server/cookies";
import { requireSameOrigin } from "@/features/account/server/request-security";
import { deleteAccountSession } from "@/features/account/server/session-store";
import { getAccountServerConfig } from "@/lib/config/server-env";

export async function POST(request: Request): Promise<Response> {
  try {
    const config = getAccountServerConfig();
    requireSameOrigin(request, config.oidcRedirectUri.origin);
  } catch {
    return NextResponse.json({ error: "request rejected" }, { status: 403 });
  }
  const handle = (await cookies()).get(sessionCookieName())?.value;
  if (handle) await deleteAccountSession(handle);
  const response = NextResponse.redirect(
    new URL("/", getAccountServerConfig().oidcRedirectUri.origin),
    303,
  );
  response.cookies.delete(sessionCookieName());
  response.headers.set("Cache-Control", "no-store");
  return response;
}
