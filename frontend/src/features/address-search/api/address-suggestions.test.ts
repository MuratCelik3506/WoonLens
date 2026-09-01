import { describe, expect, it, vi } from "vitest";

import { requestAddressSuggestions } from "@/features/address-search/api/address-suggestions";

const apiBaseUrl = new URL("http://api.example.test:8000");

describe("requestAddressSuggestions", () => {
  it("encodes the query and disables response caching", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [] }), {
        headers: { "Content-Type": "application/json" },
      }),
    );

    await requestAddressSuggestions("Westblaak 120 & A", fetcher, apiBaseUrl);

    const requestedUrl = fetcher.mock.calls[0]?.[0];
    expect(requestedUrl).toBeInstanceOf(URL);
    expect((requestedUrl as URL).searchParams.get("q")).toBe("Westblaak 120 & A");
    expect(fetcher).toHaveBeenCalledWith(
      expect.any(URL),
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("turns non-success responses into a typed safe error", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(new Response("provider detail", { status: 503 }));

    await expect(
      requestAddressSuggestions("Westblaak", fetcher, apiBaseUrl),
    ).rejects.toEqual(
      expect.objectContaining({
        message: "Address search is currently unavailable",
        status: 503,
      }),
    );
  });
});
