import { describe, expect, it } from "vitest";

import { parseLiveComparison } from "@/features/live-comparison/model/live-comparison";

const first = "11111111-1111-4111-8111-111111111111";
const second = "22222222-2222-4222-8222-222222222222";

function home(addressId: string, number: string) {
  return {
    address_id: addressId,
    overview: {
      address: {
        city: "Rotterdam",
        house_letter: null,
        house_number: number,
        house_number_suffix: null,
        postal_code: "3012BR",
        source: {
          dataset: "BAG",
          license: "CC0",
          provider: "PDOK",
          retrieved_at: "2026-09-01T12:00:00Z",
        },
        street: "Westblaak",
      },
      administrative_context: null,
      air_quality: null,
      energy_registration: null,
      neighborhood_indicators: null,
      property: null,
    },
    unavailable_reason: null,
  };
}

describe("parseLiveComparison", () => {
  it("normalizes ordered homes, metrics, missing values, and provenance", () => {
    const result = parseLiveComparison({
      audits: [],
      homes: [home(first, "120"), home(second, "40")],
      insights: [],
      metrics: [
        {
          metric: {
            definition: "Official BAG registered area.",
            key: "registered_area_m2",
            label: "Registered BAG area",
            scope: "property",
            supports_delta: true,
            unit: "m²",
          },
          values: [
            {
              address_id: first,
              delta_from_baseline: 0,
              is_baseline: true,
              missing_reason: null,
              value: 80,
            },
            {
              address_id: second,
              delta_from_baseline: null,
              is_baseline: false,
              missing_reason: "not_reported",
              value: null,
            },
          ],
        },
      ],
      notices: [{ code: "context", message: "Facts remain contextual." }],
      rules_version: "1.1.0",
    });

    expect(result.homes.map((item) => item.addressId)).toEqual([first, second]);
    expect(result.homes[0]?.displayName).toContain("Westblaak 120");
    expect(result.homes[0]?.sources[0]?.provider).toBe("PDOK");
    expect(result.metrics[0]?.values[1]?.missingReason).toBe("not_reported");
  });

  it("rejects malformed metric cardinality", () => {
    expect(() =>
      parseLiveComparison({
        homes: [home(first, "120"), home(second, "40")],
        metrics: [
          {
            metric: {
              definition: "Definition",
              key: "key",
              label: "Label",
              scope: "property",
              unit: "m²",
            },
            values: [],
          },
        ],
        notices: [],
        rules_version: "1.1.0",
      }),
    ).toThrow("one value per home");
  });
});
