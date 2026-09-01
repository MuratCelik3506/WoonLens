import { AppShell } from "@/components/layout/app-shell";
import { ComparisonBuilder } from "@/features/comparison-selection/components/comparison-builder";
import { ApiStatus } from "@/features/system-status/components/api-status";

export default function Home() {
  return (
    <AppShell
      comparisonExperience={<ComparisonBuilder />}
      systemStatus={<ApiStatus />}
    />
  );
}
