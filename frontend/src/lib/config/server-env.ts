const DEFAULT_SERVER_API_BASE_URL = "http://localhost:8000";

export type ServerConfig = Readonly<{
  apiBaseUrl: URL;
}>;

export type AccountServerConfig = Readonly<{
  apiBaseUrl: URL;
  oidcIssuer: URL;
  oidcInternalOrigin: URL;
  oidcClientId: string;
  oidcClientSecret: string;
  oidcRedirectUri: URL;
  redisUrl: string;
  sessionEncryptionKey: string;
  secureCookies: boolean;
}>;

export function getServerConfig(
  apiBaseUrl = process.env.WOONLENS_API_BASE_URL ?? DEFAULT_SERVER_API_BASE_URL,
): ServerConfig {
  const url = new URL(apiBaseUrl);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("server API base URL must use HTTP or HTTPS");
  }

  return { apiBaseUrl: url };
}

export function getAccountServerConfig(): AccountServerConfig {
  const apiBaseUrl = getServerConfig().apiBaseUrl;
  const oidcIssuer = requiredUrl("WOONLENS_OIDC_ISSUER");
  const oidcInternalOrigin = requiredUrl("WOONLENS_OIDC_INTERNAL_ORIGIN");
  const oidcRedirectUri = requiredUrl("WOONLENS_OIDC_REDIRECT_URI");
  const oidcClientId = required("WOONLENS_OIDC_CLIENT_ID");
  const oidcClientSecret = required("WOONLENS_OIDC_CLIENT_SECRET");
  const redisUrl = required("WOONLENS_REDIS_URL");
  const sessionEncryptionKey = required("WOONLENS_SESSION_ENCRYPTION_KEY");
  const production = process.env.NODE_ENV === "production";

  if (production) {
    for (const url of [oidcIssuer, oidcRedirectUri]) {
      if (url.protocol !== "https:") {
        throw new Error("production OIDC URLs must use HTTPS");
      }
    }
    if (sessionEncryptionKey === "bG9jYWwtZGV2ZWxvcG1lbnQtc2Vzc2lvbi1rZXkhISE=") {
      throw new Error("production must not use the local session encryption key");
    }
  }

  return {
    apiBaseUrl,
    oidcIssuer,
    oidcInternalOrigin,
    oidcClientId,
    oidcClientSecret,
    oidcRedirectUri,
    redisUrl,
    sessionEncryptionKey,
    secureCookies: production,
  };
}

export function accountFeaturesEnabled(): boolean {
  return process.env.WOONLENS_ACCOUNT_FEATURES_ENABLED === "true";
}

function required(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`${name} is required for account routes`);
  }
  return value;
}

function requiredUrl(name: string): URL {
  const url = new URL(required(name));
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error(`${name} must use HTTP or HTTPS`);
  }
  return url;
}
