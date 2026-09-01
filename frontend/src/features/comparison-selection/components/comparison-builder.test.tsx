import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { searchAddresses } from "@/features/address-search/api/address-suggestions";
import type { AddressSuggestion } from "@/features/address-search/model/address-suggestion";
import { ComparisonBuilder } from "@/features/comparison-selection/components/comparison-builder";
import { downloadComparison } from "@/features/comparison-downloads/api/comparison-download";
import { compareHomes } from "@/features/live-comparison/api/live-comparison";
import type { LiveComparison } from "@/features/live-comparison/model/live-comparison";

vi.mock("@/features/address-search/api/address-suggestions", () => ({
  searchAddresses: vi.fn(),
}));
vi.mock("@/features/live-comparison/api/live-comparison", () => ({
  compareHomes: vi.fn(),
}));
vi.mock("@/features/comparison-downloads/api/comparison-download", () => ({
  downloadComparison: vi.fn(),
}));

const mockedSearch = vi.mocked(searchAddresses);
const mockedComparison = vi.mocked(compareHomes);
const mockedDownload = vi.mocked(downloadComparison);

function suggestion(number: number): AddressSuggestion {
  return {
    displayName: `Examplelaan ${number}, 1234 AB Teststad`,
    id: `11111111-1111-4111-8111-${number.toString().padStart(12, "0")}`,
    source: { dataset: "PDOK Location API", provider: "PDOK" },
  };
}

function renderBuilder() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ComparisonBuilder />
    </QueryClientProvider>,
  );
}

function comparison(
  first: AddressSuggestion,
  second: AddressSuggestion,
): LiveComparison {
  return {
    audits: [
      {
        addressId: first.id,
        classification: "definition-difference",
        fields: ["bag.registered_area_m2", "ep_online.thermal_zone_area_m2"],
        message: "The fields describe different scopes and are not a register error.",
        ruleId: "area.definition.v1",
        values: [80, 75],
      },
      {
        addressId: second.id,
        classification: "missing",
        fields: ["bag.construction_year", "ep_online.construction_year"],
        message: "Both construction-year fields are required for this audit.",
        ruleId: "construction_year.cross_source.v1",
        values: [1990, null],
      },
    ],
    homes: [first, second].map((item) => ({
      addressId: item.id,
      contextNotes: [],
      details: [
        {
          facts: [
            { label: "BAG registered area", unit: "m²", value: 80 },
            { label: "Usage purposes", unit: null, value: ["residential"] },
            { label: "BAG residential-unit ID", unit: null, value: "0599010000295420" },
          ],
          level: "property",
          limitation:
            "BAG registered area is an official register value, not measured living area.",
          title: "BAG property",
        },
      ],
      displayName: item.displayName,
      sources: [
        {
          dataset: "BAG",
          license: "CC0",
          provider: "PDOK",
          retrievedAt: "2026-09-01T12:00:00Z",
        },
      ],
      unavailableReason: null,
    })),
    metrics: [
      {
        definition: "Official BAG registered area.",
        key: "registered_area_m2",
        label: "Registered BAG area",
        scope: "property",
        unit: "m²",
        values: [
          { addressId: first.id, isBaseline: true, missingReason: null, value: 80 },
          {
            addressId: second.id,
            isBaseline: false,
            missingReason: "not_reported",
            value: null,
          },
        ],
      },
    ],
    insights: [
      {
        addressIds: [first.id],
        classification: "descriptive_extreme",
        message:
          "This home has the largest reported BAG registered area; larger is a preference fact, not an overall quality verdict.",
        metricKey: "registered_area_m2",
        ruleId: "registered_area_m2.extreme",
      },
    ],
    notices: [{ code: "area", message: "Area definitions remain distinct." }],
    rulesVersion: "1.1.0",
  };
}

async function searchFor(query: string, item: AddressSuggestion) {
  mockedSearch.mockResolvedValueOnce({ items: [item] });
  const combobox = screen.getByRole("combobox");
  fireEvent.focus(combobox);
  fireEvent.change(combobox, { target: { value: query } });
  return screen.findByRole("option", { name: new RegExp(item.displayName) });
}

describe("ComparisonBuilder", () => {
  beforeEach(() => {
    mockedSearch.mockReset();
    mockedSearch.mockResolvedValue({ items: [] });
    mockedComparison.mockReset();
    mockedDownload.mockReset();
  });

  it("selects an official suggestion with the keyboard", async () => {
    renderBuilder();
    const first = suggestion(10);

    await searchFor("Examplelaan 10", first);
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "ArrowDown" });
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "Enter" });

    expect(screen.getByText(first.displayName)).toBeInTheDocument();
    expect(screen.getByText("1 of 5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Compare homes" })).toBeDisabled();
  });

  it("prevents duplicates, enforces five homes, and resumes after removal", async () => {
    renderBuilder();

    for (let index = 1; index <= 5; index += 1) {
      const item = suggestion(index);
      const option = await searchFor(`Examplelaan ${index}`, item);
      fireEvent.click(option);
    }

    expect(screen.getByText("5 of 5")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Compare homes" })).toBeEnabled();

    fireEvent.click(
      screen.getByRole("button", { name: `Remove ${suggestion(3).displayName}` }),
    );
    expect(screen.getByText("4 of 5")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeEnabled();

    const first = suggestion(1);
    const duplicate = await searchFor("Examplelaan 1", first);
    fireEvent.click(duplicate);
    expect(
      screen.getByText(`${first.displayName} is already selected.`),
    ).toBeInTheDocument();
    expect(screen.getByText("4 of 5")).toBeInTheDocument();
  });

  it("renders a neutral live result and removes it when the selection changes", async () => {
    renderBuilder();
    const first = suggestion(1);
    const second = suggestion(2);
    fireEvent.click(await searchFor("Examplelaan 1", first));
    fireEvent.click(await searchFor("Examplelaan 2", second));
    mockedComparison.mockResolvedValueOnce(comparison(first, second));

    fireEvent.click(screen.getByRole("button", { name: "Compare homes" }));

    expect(
      await screen.findByRole("heading", {
        name: "Factual differences, source by source",
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("80 m²").length).toBeGreaterThan(0);
    expect(screen.getByText("Not reported")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Explainable differences" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/larger is a preference fact, not an overall quality verdict/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Cross-source checks" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Definition difference")).toBeInTheDocument();
    expect(screen.getByText("Not available from the source")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Official details by home" }),
    ).toBeInTheDocument();
    const firstPanel = screen
      .getByText(`Home 1 · ${first.displayName}`)
      .closest("details");
    expect(firstPanel).not.toBeNull();
    if (!firstPanel) throw new Error("first home detail panel was not rendered");
    fireEvent.click(within(firstPanel).getByText(`Home 1 · ${first.displayName}`));
    expect(
      within(firstPanel).getByRole("heading", { name: "BAG property" }),
    ).toBeInTheDocument();
    expect(within(firstPanel).getByText(/property level/i)).toBeInTheDocument();
    expect(within(firstPanel).getByText("80 m²")).toBeInTheDocument();
    fireEvent.click(within(firstPanel).getByText("Technical identifiers"));
    expect(within(firstPanel).getByText("0599010000295420")).toBeInTheDocument();
    expect(screen.queryByText(/winner|best home/i)).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: `Remove ${first.displayName}` }),
    );
    expect(
      screen.queryByRole("heading", { name: "Factual differences, source by source" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Explainable differences" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Official details by home" }),
    ).not.toBeInTheDocument();
  });

  it("preserves the selection and allows retry after a comparison error", async () => {
    renderBuilder();
    const first = suggestion(1);
    const second = suggestion(2);
    fireEvent.click(await searchFor("Examplelaan 1", first));
    fireEvent.click(await searchFor("Examplelaan 2", second));
    mockedComparison.mockRejectedValueOnce(new Error("provider unavailable"));

    fireEvent.click(screen.getByRole("button", { name: "Compare homes" }));
    expect(await screen.findByText(/selection is preserved/i)).toBeInTheDocument();
    expect(screen.getByText("2 of 5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try comparison again" })).toBeEnabled();
  });

  it("downloads a transient report and revokes its object URL", async () => {
    renderBuilder();
    const first = suggestion(1);
    const second = suggestion(2);
    fireEvent.click(await searchFor("Examplelaan 1", first));
    fireEvent.click(await searchFor("Examplelaan 2", second));
    mockedComparison.mockResolvedValueOnce(comparison(first, second));
    fireEvent.click(screen.getByRole("button", { name: "Compare homes" }));
    await screen.findByRole("heading", {
      name: "Factual differences, source by source",
    });

    const createObjectUrl = vi.fn(() => "blob:report");
    const revokeObjectUrl = vi.fn();
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: createObjectUrl,
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: revokeObjectUrl,
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    mockedDownload.mockResolvedValueOnce({
      blob: new Blob(["{}"], { type: "application/json" }),
      filename: "woonlens-comparison-20260901T120000Z.json",
    });

    fireEvent.click(screen.getByRole("button", { name: "Download JSON" }));

    expect(await screen.findByText("JSON download started.")).toBeInTheDocument();
    expect(mockedDownload).toHaveBeenCalledWith("json", [first.id, second.id]);
    expect(createObjectUrl).toHaveBeenCalledOnce();
    await waitFor(() => expect(revokeObjectUrl).toHaveBeenCalledWith("blob:report"));
  });
});
