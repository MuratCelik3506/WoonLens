"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type SessionState = "checking" | "unavailable" | "guest" | "authenticated";

export function AccountAccess() {
  const router = useRouter();
  const [state, setState] = useState<SessionState>("checking");
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(false);

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
      <div className="flex flex-wrap items-center justify-end gap-2">
        <a
          className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 text-sm font-medium no-underline hover:bg-accent-soft"
          download
          href="/api/account/export"
        >
          Export my data
        </a>
        {!confirmingDelete ? (
          <button
            className="inline-flex min-h-11 items-center rounded-lg border border-red-300 px-4 text-sm font-medium text-red-700 hover:bg-red-50"
            onClick={() => setConfirmingDelete(true)}
            type="button"
          >
            Delete WoonLens data
          </button>
        ) : (
          <div
            className="w-full max-w-md rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-950"
            role="alert"
          >
            <p>
              This permanently deletes your favourites and saved comparisons. Your
              external sign-in account is not deleted.
            </p>
            {deleteError ? (
              <p className="mt-2 font-medium">Deletion failed. Please try again.</p>
            ) : null}
            <div className="mt-3 flex gap-2">
              <button
                className="min-h-10 rounded-md bg-red-700 px-3 font-medium text-white disabled:opacity-60"
                disabled={deleting}
                onClick={() => {
                  setDeleting(true);
                  setDeleteError(false);
                  void fetch("/api/account", { method: "DELETE" })
                    .then((response) => {
                      if (!response.ok) throw new Error("deletion failed");
                      router.push("/?account=deleted");
                      router.refresh();
                    })
                    .catch(() => {
                      setDeleting(false);
                      setDeleteError(true);
                    });
                }}
                type="button"
              >
                {deleting ? "Deleting…" : "Permanently delete"}
              </button>
              <button
                className="min-h-10 rounded-md border border-border bg-white px-3 font-medium"
                disabled={deleting}
                onClick={() => setConfirmingDelete(false)}
                type="button"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        <form action="/api/auth/logout" method="post">
          <button
            className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 text-sm font-medium hover:bg-accent-soft"
            type="submit"
          >
            Sign out
          </button>
        </form>
      </div>
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
