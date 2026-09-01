import { describe, expect, it } from "vitest";

import { parseAddressSuggestions } from "@/features/address-search/model/address-suggestion";

describe("parseAddressSuggestions", () => {
  it("owns and narrows the backend suggestion contract", () => {
    expect(
      parseAddressSuggestions({
        items: [
          {
            coordinates: { latitude: 52.1, longitude: 4.3 },
            display_name: "Westblaak 120, 3012 KM Rotterdam",
            id: "11111111-1111-4111-8111-111111111111",
            source: { dataset: "PDOK Location API", provider: "PDOK" },
          },
        ],
      }),
    ).toEqual({
      items: [
        {
          displayName: "Westblaak 120, 3012 KM Rotterdam",
          id: "11111111-1111-4111-8111-111111111111",
          source: { dataset: "PDOK Location API", provider: "PDOK" },
        },
      ],
    });
  });

  it("rejects malformed provider-facing data", () => {
    expect(() =>
      parseAddressSuggestions({
        items: [{ display_name: "Incomplete address", id: 42, source: null }],
      }),
    ).toThrow("Address suggestion response is invalid");
  });
});
