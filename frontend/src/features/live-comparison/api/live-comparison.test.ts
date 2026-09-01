import { describe, expect, it, vi } from "vitest";

import {
  LiveComparisonError,
  requestLiveComparison,
  validateAddressIds,
} from "@/features/live-comparison/api/live-comparison";

const first = "11111111-1111-4111-8111-111111111111";
const second = "22222222-2222-4222-8222-222222222222";

describe("live comparison API", () => {
  it("rejects invalid count and duplicate identifiers before a request", () => {
    expect(() => validateAddressIds([first])).toThrow(LiveComparisonError);
    expect(() => validateAddressIds([first, first])).toThrow("unique");
  });

  it("posts only validated identifiers with no-store semantics", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          homes: [
            {
              addressId: first,
              contextNotes: [],
              displayName: null,
              sources: [],
              unavailableReason: "source_unavailable",
            },
            {
              addressId: second,
              contextNotes: [],
              displayName: null,
              sources: [],
              unavailableReason: "source_unavailable",
            },
          ],
          metrics: [],
          notices: [],
          rulesVersion: "1.1.0",
        }),
        { status: 200 },
      ),
    );

    await requestLiveComparison([first, second], fetcher, new URL("http://api:8000"));

    expect(fetcher).toHaveBeenCalledWith(
      new URL("http://api:8000/api/v1/comparisons/live"),
      expect.objectContaining({
        body: JSON.stringify({ address_ids: [first, second] }),
        cache: "no-store",
        method: "POST",
      }),
    );
  });

  it("normalizes an invalid provider response as a safe gateway error", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response(JSON.stringify({ homes: [] }), { status: 200 }));
    await expect(
      requestLiveComparison([first, second], fetcher, new URL("http://api:8000")),
    ).rejects.toMatchObject({ status: 502 });
  });
});
