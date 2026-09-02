export function requireSameOrigin(
  request: Request,
  expectedOrigin = new URL(request.url).origin,
): void {
  const origin = request.headers.get("origin");
  if (!origin || origin !== expectedOrigin) {
    throw new Error("cross-origin account mutation rejected");
  }
}

export function safeReturnPath(value: string | null): string {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/";
}
