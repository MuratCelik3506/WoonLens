import { describe, expect, it, vi } from "vitest";

import {
  ComparisonDownloadError,
  requestComparisonDownload,
} from "@/features/comparison-downloads/api/comparison-download";

const ids = [
  "11111111-1111-4111-8111-111111111111",
  "22222222-2222-4222-8222-222222222222",
] as const;

describe("comparison downloads", () => {
  it("requests a transient PDF and preserves a safe filename", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(new Uint8Array([37, 80, 68, 70]), {
        headers: {
          "Content-Disposition":
            'attachment; filename="woonlens-comparison-20260901T120000Z.pdf"',
          "Content-Type": "application/pdf",
        },
      }),
    );
    const report = await requestComparisonDownload(
      "pdf",
      ids,
      fetcher,
      new URL("http://api:8000"),
    );
    expect(report.filename).toBe("woonlens-comparison-20260901T120000Z.pdf");
    expect(fetcher).toHaveBeenCalledWith(
      new URL("http://api:8000/api/v1/comparison-downloads/pdf"),
      expect.objectContaining({
        body: JSON.stringify({ address_ids: ids }),
        cache: "no-store",
        method: "POST",
      }),
    );
  });

  it("replaces an unsafe filename with a fixed fallback", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response("{}", {
        headers: {
          "Content-Disposition": 'attachment; filename="../../report.json"',
          "Content-Type": "application/json",
        },
      }),
    );
    await expect(
      requestComparisonDownload("json", ids, fetcher, new URL("http://api:8000")),
    ).resolves.toMatchObject({ filename: "woonlens-comparison.json" });
  });

  it("rejects an unexpected response content type", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        new Response("error", { headers: { "Content-Type": "text/html" } }),
      );
    await expect(
      requestComparisonDownload("pdf", ids, fetcher, new URL("http://api:8000")),
    ).rejects.toBeInstanceOf(ComparisonDownloadError);
  });
});
