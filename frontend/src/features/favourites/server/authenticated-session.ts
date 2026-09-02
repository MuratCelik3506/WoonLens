import { cookies } from "next/headers";

import { sessionCookieName } from "@/features/account/server/cookies";
import { readAccountSession } from "@/features/account/server/session-store";

export async function accessToken(): Promise<string | null> {
  const handle = (await cookies()).get(sessionCookieName())?.value;
  return handle ? ((await readAccountSession(handle))?.accessToken ?? null) : null;
}
