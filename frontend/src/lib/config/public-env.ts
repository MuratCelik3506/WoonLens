const DEFAULT_PUBLIC_API_BASE_URL = "http://localhost:8000";

export type PublicConfig = Readonly<{
  apiBaseUrl: URL;
}>;

export function getPublicConfig(
  apiBaseUrl = process.env.NEXT_PUBLIC_WOONLENS_API_BASE_URL ??
    DEFAULT_PUBLIC_API_BASE_URL,
): PublicConfig {
  return { apiBaseUrl: parseHttpUrl(apiBaseUrl, "public API base URL") };
}

function parseHttpUrl(value: string, label: string): URL {
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error(`${label} must use HTTP or HTTPS`);
  }

  return url;
}
