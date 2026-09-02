import { afterEach, describe, expect, it, vi } from "vitest";

import {
  accountFeaturesEnabled,
  getAccountServerConfig,
  getServerConfig,
} from "@/lib/config/server-env";

function accountEnvironment(): void {
  vi.stubEnv("WOONLENS_API_BASE_URL", "http://api:8000");
  vi.stubEnv("WOONLENS_OIDC_ISSUER", "http://localhost:8080/realms/woonlens");
  vi.stubEnv("WOONLENS_OIDC_INTERNAL_ORIGIN", "http://keycloak:8080");
  vi.stubEnv("WOONLENS_OIDC_CLIENT_ID", "woonlens-web");
  vi.stubEnv("WOONLENS_OIDC_CLIENT_SECRET", "test-secret");
  vi.stubEnv("WOONLENS_OIDC_REDIRECT_URI", "http://localhost:3000/api/auth/callback");
  vi.stubEnv("WOONLENS_REDIS_URL", "redis://redis:6379/0");
  vi.stubEnv(
    "WOONLENS_SESSION_ENCRYPTION_KEY",
    "bG9jYWwtZGV2ZWxvcG1lbnQtc2Vzc2lvbi1rZXkhISE=",
  );
}

afterEach(() => vi.unstubAllEnvs());

describe("server configuration", () => {
  it("keeps account credentials server-side and accepts local development URLs", () => {
    accountEnvironment();
    vi.stubEnv("NODE_ENV", "development");
    const config = getAccountServerConfig();
    expect(config.oidcClientId).toBe("woonlens-web");
    expect(config.secureCookies).toBe(false);
  });

  it("requires HTTPS for production front-channel URLs", () => {
    accountEnvironment();
    vi.stubEnv("NODE_ENV", "production");
    expect(() => getAccountServerConfig()).toThrow(
      "production OIDC URLs must use HTTPS",
    );
  });

  it("rejects the documented local encryption key in production", () => {
    accountEnvironment();
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("WOONLENS_OIDC_ISSUER", "https://identity.woonlens.test/realms/main");
    vi.stubEnv("WOONLENS_OIDC_REDIRECT_URI", "https://woonlens.test/api/auth/callback");
    expect(() => getAccountServerConfig()).toThrow(
      "production must not use the local session encryption key",
    );
  });

  it("rejects unsupported backend URL protocols", () => {
    expect(() => getServerConfig("file:///tmp/data")).toThrow(
      "server API base URL must use HTTP or HTTPS",
    );
  });

  it("keeps account controls opt-in per deployment", () => {
    expect(accountFeaturesEnabled()).toBe(false);
    vi.stubEnv("WOONLENS_ACCOUNT_FEATURES_ENABLED", "true");
    expect(accountFeaturesEnabled()).toBe(true);
  });
});
