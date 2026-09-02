import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  deleteBackendAccount: vi.fn(),
  deleteAccountSession: vi.fn(),
  readAccountSession: vi.fn(),
}));

vi.mock("next/headers", () => ({
  cookies: async () => ({ get: () => ({ value: "session-handle" }) }),
}));
vi.mock("@/features/account/server/backend-account", () => ({
  deleteBackendAccount: mocks.deleteBackendAccount,
  fetchBackendAccount: vi.fn(),
}));
vi.mock("@/features/account/server/session-store", () => ({
  deleteAccountSession: mocks.deleteAccountSession,
  readAccountSession: mocks.readAccountSession,
}));
vi.mock("@/features/account/server/cookies", () => ({
  sessionCookieName: () => "woonlens_dev_session",
}));
vi.mock("@/lib/config/server-env", () => ({
  getAccountServerConfig: () => ({
    oidcRedirectUri: new URL("http://localhost:3000/api/auth/callback"),
  }),
}));

import { DELETE } from "@/app/api/account/route";

beforeEach(() => {
  vi.clearAllMocks();
  mocks.readAccountSession.mockResolvedValue({ accessToken: "access-token" });
  mocks.deleteBackendAccount.mockResolvedValue(undefined);
  mocks.deleteAccountSession.mockResolvedValue(undefined);
});

describe("DELETE /api/account", () => {
  it("rejects cross-origin deletion", async () => {
    const response = await DELETE(
      new Request("http://localhost:3000/api/account", {
        method: "DELETE",
        headers: { Origin: "https://attacker.example" },
      }),
    );

    expect(response.status).toBe(403);
    expect(mocks.deleteBackendAccount).not.toHaveBeenCalled();
  });

  it("deletes backend data before ending the local session", async () => {
    const response = await DELETE(
      new Request("http://localhost:3000/api/account", {
        method: "DELETE",
        headers: { Origin: "http://localhost:3000" },
      }),
    );

    expect(response.status).toBe(204);
    expect(mocks.deleteBackendAccount).toHaveBeenCalledWith("access-token");
    expect(mocks.deleteAccountSession).toHaveBeenCalledWith("session-handle");
    expect(mocks.deleteBackendAccount.mock.invocationCallOrder[0]).toBeLessThan(
      mocks.deleteAccountSession.mock.invocationCallOrder[0],
    );
  });

  it("keeps the session when backend deletion fails", async () => {
    mocks.deleteBackendAccount.mockRejectedValue(new Error("backend unavailable"));

    const response = await DELETE(
      new Request("http://localhost:3000/api/account", {
        method: "DELETE",
        headers: { Origin: "http://localhost:3000" },
      }),
    );

    expect(response.status).toBe(502);
    expect(mocks.deleteAccountSession).not.toHaveBeenCalled();
  });
});
