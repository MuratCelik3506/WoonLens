import { cookies } from "next/headers";

import { sessionCookieName } from "@/features/account/server/cookies";
import { readAccountSession } from "@/features/account/server/session-store";

export async function accessToken(): Promise<string | null> {
  return (await authenticatedSession())?.accessToken ?? null;
}

export async function authenticatedSession(): Promise<{
  handle: string;
  accessToken: string;
} | null> {
  const handle = (await cookies()).get(sessionCookieName())?.value;
  if (!handle) return null;
  const session = await readAccountSession(handle);
  return session ? { handle, accessToken: session.accessToken } : null;
}
