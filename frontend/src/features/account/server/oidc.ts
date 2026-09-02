import * as client from "openid-client";

import { getAccountServerConfig } from "@/lib/config/server-env";

let configuration: Promise<client.Configuration> | undefined;

export function oidcConfiguration(): Promise<client.Configuration> {
  configuration ??= discover();
  return configuration;
}

async function discover(): Promise<client.Configuration> {
  const config = getAccountServerConfig();
  const execute = config.secureCookies ? [] : [client.allowInsecureRequests];
  return client.discovery(
    config.oidcIssuer,
    config.oidcClientId,
    config.oidcClientSecret,
    undefined,
    {
      execute,
      [client.customFetch]: async (url, options) => {
        const requested = new URL(url);
        if (requested.origin === config.oidcIssuer.origin) {
          const internal = new URL(
            requested.pathname + requested.search,
            config.oidcInternalOrigin,
          );
          // openid-client supports Fetch API body types broader than TypeScript's
          // Node fetch declaration while remaining runtime-compatible.
          // @ts-expect-error See openid-client customFetch documentation.
          return fetch(internal, options);
        }
        // @ts-expect-error See openid-client customFetch documentation.
        return fetch(requested, options);
      },
    },
  );
}
