import { describe, expect, it } from "vitest";

import {
  requireSameOrigin,
  safeReturnPath,
} from "@/features/account/server/request-security";

describe("account request security", () => {
  it("allows only local absolute return paths", () => {
    expect(safeReturnPath("/account?ready=true")).toBe("/account?ready=true");
    expect(safeReturnPath("//attacker.example/path")).toBe("/");
    expect(safeReturnPath("https://attacker.example/path")).toBe("/");
    expect(safeReturnPath(null)).toBe("/");
  });

  it("requires an exact same-origin mutation", () => {
    expect(() =>
      requireSameOrigin(
        new Request("https://woonlens.test/api/auth/logout", {
          headers: { Origin: "https://woonlens.test" },
        }),
      ),
    ).not.toThrow();
    expect(() =>
      requireSameOrigin(
        new Request("https://woonlens.test/api/auth/logout", {
          headers: { Origin: "https://attacker.test" },
        }),
      ),
    ).toThrow("cross-origin");
  });

  it("uses the configured public origin behind a reverse proxy", () => {
    expect(() =>
      requireSameOrigin(
        new Request("http://0.0.0.0:3000/api/auth/logout", {
          headers: { Origin: "http://localhost:3000" },
        }),
        "http://localhost:3000",
      ),
    ).not.toThrow();
  });
});
