"use client";

import { useEffect, useState } from "react";

type SessionState = "checking" | "unavailable" | "guest" | "authenticated";

export function AccountAccess() {
  const [state, setState] = useState<SessionState>("checking");

  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/auth/session", {
      cache: "no-store",
      signal: controller.signal,
    })
      .then(
        async (response) =>
          (await response.json()) as {
            available?: boolean;
            authenticated?: boolean;
          },
      )
      .then((session) => {
        if (session.available === false) setState("unavailable");
        else setState(session.authenticated ? "authenticated" : "guest");
      })
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setState("guest");
        }
      });
    return () => controller.abort();
  }, []);

  if (state === "unavailable") return null;

  if (state === "authenticated") {
    return (
      <form action="/api/auth/logout" method="post">
        <button
          className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 text-sm font-medium hover:bg-accent-soft"
          type="submit"
        >
          Sign out
        </button>
      </form>
    );
  }

  return (
    <a
      aria-disabled={state === "checking"}
      className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 text-sm font-medium no-underline hover:bg-accent-soft aria-disabled:opacity-60"
      href="/api/auth/login"
    >
      {state === "checking" ? "Checking account…" : "Sign in"}
    </a>
  );
}
