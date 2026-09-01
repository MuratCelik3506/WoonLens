import { describe, expect, it } from "vitest";

import { getPublicConfig } from "@/lib/config/public-env";

describe("getPublicConfig", () => {
  it("accepts an HTTP API base URL", () => {
    expect(getPublicConfig("http://api.example.test:8000").apiBaseUrl.href).toBe(
      "http://api.example.test:8000/",
    );
  });

  it("rejects a non-HTTP API base URL", () => {
    expect(() => getPublicConfig("file:///tmp/provider-data")).toThrow(
      "public API base URL must use HTTP or HTTPS",
    );
  });
});
