import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { fetchBackendAccount } from "@/features/account/server/backend-account";
import { sessionCookieName } from "@/features/account/server/cookies";
import { readAccountSession } from "@/features/account/server/session-store";
import { accountFeaturesEnabled } from "@/lib/config/server-env";

export async function GET(): Promise<Response> {
  if (!accountFeaturesEnabled()) {
    return sessionResponse({ available: false, authenticated: false });
  }
  const handle = (await cookies()).get(sessionCookieName())?.value;
  if (!handle) return sessionResponse({ available: true, authenticated: false });
  const session = await readAccountSession(handle);
  if (!session) return sessionResponse({ available: true, authenticated: false });
  try {
    const account = await fetchBackendAccount(session.accessToken);
    return sessionResponse({ available: true, authenticated: true, account });
  } catch {
    return sessionResponse({ available: true, authenticated: false });
  }
}

function sessionResponse(body: unknown): NextResponse {
  const response = NextResponse.json(body);
  response.headers.set("Cache-Control", "no-store");
  return response;
}
