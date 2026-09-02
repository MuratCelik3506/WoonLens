import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import * as client from "openid-client";

import { ensureBackendAccount } from "@/features/account/server/backend-account";
import {
  loginCookieName,
  privateCookie,
  sessionCookieName,
} from "@/features/account/server/cookies";
import { oidcConfiguration } from "@/features/account/server/oidc";
import {
  consumeLoginTransaction,
  newOpaqueHandle,
  saveAccountSession,
} from "@/features/account/server/session-store";
import { getAccountServerConfig } from "@/lib/config/server-env";

export async function GET(request: Request): Promise<Response> {
  const cookieStore = await cookies();
  const loginHandle = cookieStore.get(loginCookieName())?.value;
  if (!loginHandle) return failed(request);
  const transaction = await consumeLoginTransaction(loginHandle);
  if (!transaction) return failed(request);

  try {
    const configuredCallback = new URL(getAccountServerConfig().oidcRedirectUri);
    configuredCallback.search = new URL(request.url).search;
    const tokens = await client.authorizationCodeGrant(
      await oidcConfiguration(),
      configuredCallback,
      {
        pkceCodeVerifier: transaction.codeVerifier,
        expectedState: transaction.state,
        expectedNonce: transaction.nonce,
        idTokenExpected: true,
      },
    );
    if (!tokens.access_token || !tokens.expires_in) return failed(request);
    await ensureBackendAccount(tokens.access_token);

    const sessionHandle = newOpaqueHandle();
    await saveAccountSession(sessionHandle, tokens.access_token, tokens.expires_in);
    const response = NextResponse.redirect(
      new URL(transaction.returnTo, getAccountServerConfig().oidcRedirectUri.origin),
      303,
    );
    response.cookies.delete(loginCookieName());
    const options = privateCookie(sessionHandle, Math.min(tokens.expires_in, 15 * 60));
    response.cookies.set({
      ...options,
      name: sessionCookieName(),
      value: sessionHandle,
    });
    return response;
  } catch (error) {
    console.error(
      "OIDC callback failed:",
      error instanceof Error ? error.message : "unknown error",
    );
    return failed(request);
  }
}

function failed(request: Request): NextResponse {
  let origin: URL;
  try {
    origin = getAccountServerConfig().oidcRedirectUri;
  } catch {
    origin = new URL(request.url);
  }
  const response = NextResponse.redirect(new URL("/?account=failed", origin), 303);
  response.cookies.delete(loginCookieName());
  return response;
}
