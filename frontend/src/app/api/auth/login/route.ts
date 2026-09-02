import { NextResponse } from "next/server";
import * as client from "openid-client";

import { loginCookieName, privateCookie } from "@/features/account/server/cookies";
import { oidcConfiguration } from "@/features/account/server/oidc";
import { safeReturnPath } from "@/features/account/server/request-security";
import {
  newOpaqueHandle,
  saveLoginTransaction,
} from "@/features/account/server/session-store";
import { getAccountServerConfig } from "@/lib/config/server-env";

export async function GET(request: Request): Promise<Response> {
  const configuration = await oidcConfiguration();
  const codeVerifier = client.randomPKCECodeVerifier();
  const state = client.randomState();
  const nonce = client.randomNonce();
  const handle = newOpaqueHandle();
  const returnTo = safeReturnPath(new URL(request.url).searchParams.get("returnTo"));

  await saveLoginTransaction(handle, { codeVerifier, state, nonce, returnTo });
  const codeChallenge = await client.calculatePKCECodeChallenge(codeVerifier);
  const redirect = client.buildAuthorizationUrl(configuration, {
    response_type: "code",
    redirect_uri: getAccountServerConfig().oidcRedirectUri.href,
    scope: "openid woonlens:account",
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
    state,
    nonce,
  });

  const response = NextResponse.redirect(redirect, 303);
  const options = privateCookie(handle, 5 * 60);
  response.cookies.set({ ...options, name: loginCookieName(), value: handle });
  return response;
}
