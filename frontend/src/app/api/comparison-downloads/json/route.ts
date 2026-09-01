import { proxyComparisonDownload } from "@/features/comparison-downloads/api/report-route";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return proxyComparisonDownload(request, "json");
}
