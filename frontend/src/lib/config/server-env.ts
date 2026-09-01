const DEFAULT_SERVER_API_BASE_URL = "http://localhost:8000";

export type ServerConfig = Readonly<{
  apiBaseUrl: URL;
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
