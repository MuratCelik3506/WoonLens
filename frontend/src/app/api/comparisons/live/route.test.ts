import { beforeEach, describe, expect, it, vi } from "vitest";

import { requestLiveComparison } from "@/features/live-comparison/api/live-comparison";
import { POST } from "./route";

vi.mock("@/features/live-comparison/api/live-comparison", async (importOriginal) => {
  const original =
    await importOriginal<
      typeof import("@/features/live-comparison/api/live-comparison")
    >();
  return { ...original, requestLiveComparison: vi.fn() };
});

const mockedRequest = vi.mocked(requestLiveComparison);
const first = "11111111-1111-4111-8111-111111111111";
const second = "22222222-2222-4222-8222-222222222222";

function request(addressIds: readonly string[]) {
  return new Request("http://localhost/api/comparisons/live", {
    body: JSON.stringify({ address_ids: addressIds }),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
}

describe("comparison proxy route", () => {
  beforeEach(() => mockedRequest.mockReset());

  it("rejects duplicate identifiers without calling the backend", async () => {
    const response = await POST(request([first, first]));
    expect(response.status).toBe(422);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(mockedRequest).not.toHaveBeenCalled();
  });

  it("returns a validated transient comparison", async () => {
    mockedRequest.mockResolvedValueOnce({
      audits: [],
      homes: [first, second].map((addressId) => ({
        addressId,
        contextNotes: [],
        details: [],
        displayName: null,
        sources: [],
        unavailableReason: "source_unavailable",
      })),
      metrics: [],
      notices: [],
      insights: [],
      rulesVersion: "1.1.0",
    });
    const response = await POST(request([first, second]));
    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(mockedRequest).toHaveBeenCalledWith(
      [first, second],
      fetch,
      undefined,
      expect.any(AbortSignal),
    );
  });
});
