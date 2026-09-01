import { NextResponse } from "next/server";

import {
  ComparisonDownloadError,
  requestComparisonDownload,
  type ComparisonDownloadFormat,
} from "@/features/comparison-downloads/api/comparison-download";
import {
  LiveComparisonError,
  validateAddressIds,
} from "@/features/live-comparison/api/live-comparison";

export async function proxyComparisonDownload(
  request: Request,
  format: ComparisonDownloadFormat,
) {
  try {
    const payload: unknown = await request.json();
    if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
      throw new LiveComparisonError("Invalid report request", 422);
    }
    const addressIds = validateAddressIds(
      (payload as Record<string, unknown>).address_ids,
    );
    const report = await requestComparisonDownload(
      format,
      addressIds,
      fetch,
      undefined,
      request.signal,
    );
    return new NextResponse(report.blob, {
      headers: {
        "Cache-Control": "no-store",
        "Content-Disposition": `attachment; filename="${report.filename}"`,
        "Content-Type": report.blob.type,
      },
    });
  } catch (error) {
    const status =
      error instanceof LiveComparisonError || error instanceof ComparisonDownloadError
        ? error.status
        : 422;
    return NextResponse.json(
      {
        title:
          status === 422
            ? "Select between two and five unique official addresses"
            : "Comparison report is currently unavailable",
      },
      { headers: { "Cache-Control": "no-store" }, status },
    );
  }
}
