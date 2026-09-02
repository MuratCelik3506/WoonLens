import type { ResponseCookie } from "next/dist/compiled/@edge-runtime/cookies";

import { getAccountServerConfig } from "@/lib/config/server-env";

export function sessionCookieName(): string {
  return getAccountServerConfig().secureCookies
    ? "__Host-woonlens_session"
    : "woonlens_dev_session";
}

export function loginCookieName(): string {
  return getAccountServerConfig().secureCookies
    ? "__Host-woonlens_login"
    : "woonlens_dev_login";
}

export function privateCookie(handle: string, maxAge: number): ResponseCookie {
  return {
    name: "unused",
    value: handle,
    httpOnly: true,
    secure: getAccountServerConfig().secureCookies,
    sameSite: "lax",
    path: "/",
    maxAge,
  };
}
