import { AppShell } from "@/components/layout/app-shell";
import { ApiStatus } from "@/features/system-status/components/api-status";

export default function Home() {
  return <AppShell systemStatus={<ApiStatus />} />;
}
