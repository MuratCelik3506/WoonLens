import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AccountAccess } from "@/features/account/components/account-access";

afterEach(() => vi.restoreAllMocks());

describe("AccountAccess", () => {
  it("keeps the optional guest journey visible", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ available: true, authenticated: false }),
    );
    render(<AccountAccess />);
    const link = await screen.findByRole("link", { name: "Sign in" });
    expect(link).toHaveAttribute("href", "/api/auth/login");
  });

  it("offers server-side logout for an authenticated session", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({
        available: true,
        authenticated: true,
        account: { id: "account-id" },
      }),
    );
    render(<AccountAccess />);
    const button = await screen.findByRole("button", { name: "Sign out" });
    expect(button.closest("form")).toHaveAttribute("action", "/api/auth/logout");
    expect(button.closest("form")).toHaveAttribute("method", "post");
  });

  it("hides account controls when the deployment disables accounts", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ available: false, authenticated: false }),
    );
    render(<AccountAccess />);
    await waitFor(() => {
      expect(screen.queryByRole("link")).not.toBeInTheDocument();
    });
  });
});
