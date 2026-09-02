import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { fetchBackendAccount } from "@/features/account/server/backend-account";
import { deleteBackendAccount } from "@/features/account/server/backend-account";
import { sessionCookieName } from "@/features/account/server/cookies";
import { readAccountSession } from "@/features/account/server/session-store";
import { deleteAccountSession } from "@/features/account/server/session-store";
import { requireSameOrigin } from "@/features/account/server/request-security";
import { getAccountServerConfig } from "@/lib/config/server-env";

export async function GET(): Promise<Response> {
  const handle = (await cookies()).get(sessionCookieName())?.value;
  const session = handle ? await readAccountSession(handle) : null;
  if (!session) {
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  }
  try {
    const account = await fetchBackendAccount(session.accessToken);
    const response = NextResponse.json(account);
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  }
}

export async function DELETE(request: Request): Promise<Response> {
  try {
    requireSameOrigin(request, getAccountServerConfig().oidcRedirectUri.origin);
  } catch {
    return NextResponse.json({ error: "request rejected" }, { status: 403 });
  }
  const handle = (await cookies()).get(sessionCookieName())?.value;
  const session = handle ? await readAccountSession(handle) : null;
  if (!handle || !session) {
    return NextResponse.json({ error: "authentication required" }, { status: 401 });
  }
  try {
    await deleteBackendAccount(session.accessToken);
    await deleteAccountSession(handle);
    const response = new NextResponse(null, { status: 204 });
    response.cookies.delete(sessionCookieName());
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return NextResponse.json(
      { error: "account deletion unavailable" },
      { status: 502 },
    );
  }
}
