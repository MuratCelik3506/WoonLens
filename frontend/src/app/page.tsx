import { AppShell } from "@/components/layout/app-shell";
import { ComparisonBuilder } from "@/features/comparison-selection/components/comparison-builder";
import { AccountAccess } from "@/features/account/components/account-access";
import { ApiStatus } from "@/features/system-status/components/api-status";

export default function Home() {
  return (
    <AppShell
      accountAccess={<AccountAccess />}
      comparisonExperience={<ComparisonBuilder />}
      systemStatus={<ApiStatus />}
    />
  );
}
