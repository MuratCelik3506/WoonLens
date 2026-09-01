import { beforeEach, describe, expect, it, vi } from "vitest";

import { requestComparisonDownload } from "@/features/comparison-downloads/api/comparison-download";
import { proxyComparisonDownload } from "@/features/comparison-downloads/api/report-route";

vi.mock(
  "@/features/comparison-downloads/api/comparison-download",
  async (importOriginal) => {
    const original =
      await importOriginal<
        typeof import("@/features/comparison-downloads/api/comparison-download")
      >();
    return { ...original, requestComparisonDownload: vi.fn() };
  },
);

const mockedRequest = vi.mocked(requestComparisonDownload);
const ids = [
  "11111111-1111-4111-8111-111111111111",
  "22222222-2222-4222-8222-222222222222",
] as const;

function request(addressIds: readonly string[]) {
  return new Request("http://localhost/api/comparison-downloads/pdf", {
    body: JSON.stringify({ address_ids: addressIds }),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
}

describe("report proxy route", () => {
  beforeEach(() => mockedRequest.mockReset());

  it("rejects an invalid request without calling the backend", async () => {
    const response = await proxyComparisonDownload(request([ids[0]]), "pdf");
    expect(response.status).toBe(422);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(mockedRequest).not.toHaveBeenCalled();
  });

  it("streams a verified attachment without caching", async () => {
    mockedRequest.mockResolvedValueOnce({
      blob: new Blob([new Uint8Array([37, 80, 68, 70])], {
        type: "application/pdf",
      }),
      filename: "woonlens-comparison-20260901T120000Z.pdf",
    });
    const response = await proxyComparisonDownload(request(ids), "pdf");
    expect(response.status).toBe(200);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(response.headers.get("Content-Type")).toBe("application/pdf");
    expect(response.headers.get("Content-Disposition")).toContain(
      "woonlens-comparison-20260901T120000Z.pdf",
    );
  });
});
