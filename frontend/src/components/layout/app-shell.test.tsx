import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppShell } from "@/components/layout/app-shell";

describe("AppShell", () => {
  it("renders the guest-first navigation and main comparison landmark", () => {
    render(<AppShell systemStatus={<p>API connection available</p>} />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Compare Dutch homes with trusted public data.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByText("API connection available")).toBeInTheDocument();
  });

  it("keeps unfinished comparison actions explicitly unavailable", () => {
    render(<AppShell />);

    expect(screen.getByRole("searchbox")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Search" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Compare homes" })).toBeDisabled();
  });
});
