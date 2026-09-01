"use client";

import { useQuery } from "@tanstack/react-query";

import type { HealthStatus } from "@/features/system-status/api/health";

async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch("/api/backend-health", { cache: "no-store" });
  if (!response.ok) {
    return { available: false, status: "unavailable" };
  }

  return (await response.json()) as HealthStatus;
}

export function ApiStatus() {
  const { data, isPending, refetch } = useQuery({
    queryFn: fetchHealth,
    queryKey: ["system-health"],
    retry: false,
  });

  if (isPending) {
    return (
      <p aria-live="polite" className="text-sm text-muted">
        Checking API connection…
      </p>
    );
  }

  if (data?.available) {
    return (
      <p aria-live="polite" className="text-sm text-muted">
        API connection available
      </p>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3" role="status">
      <p className="text-sm text-muted">
        API currently unavailable. The interface remains usable.
      </p>
      <button
        className="min-h-11 rounded-lg border border-border px-4 text-sm font-semibold hover:bg-accent-soft"
        onClick={() => void refetch()}
        type="button"
      >
        Try again
      </button>
    </div>
  );
}
