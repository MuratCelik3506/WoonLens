import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { fetchBackendAccount } from "@/features/account/server/backend-account";
import { sessionCookieName } from "@/features/account/server/cookies";
import { readAccountSession } from "@/features/account/server/session-store";

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
