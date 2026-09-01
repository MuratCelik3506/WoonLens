import { describe, expect, it, vi } from "vitest";

import { getHealthStatus } from "@/features/system-status/api/health";

const apiBaseUrl = new URL("http://api.example.test:8000");

describe("getHealthStatus", () => {
  it("reports an available API only for the expected healthy contract", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
      }),
    );

    await expect(getHealthStatus(fetcher, apiBaseUrl)).resolves.toEqual({
      available: true,
      status: "ok",
    });
    expect(fetcher).toHaveBeenCalledWith(
      new URL("http://api.example.test:8000/api/v1/health"),
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("keeps the shell available when the API contract is unhealthy", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response("Service unavailable", { status: 503 }));

    await expect(getHealthStatus(fetcher, apiBaseUrl)).resolves.toEqual({
      available: false,
      status: "unavailable",
    });
  });

  it("turns network failures into an unavailable state", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockRejectedValue(new TypeError("Network unavailable"));

    await expect(getHealthStatus(fetcher, apiBaseUrl)).resolves.toEqual({
      available: false,
      status: "unavailable",
    });
  });
});
