import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { searchAddresses } from "@/features/address-search/api/address-suggestions";
import type { AddressSuggestion } from "@/features/address-search/model/address-suggestion";
import { ComparisonBuilder } from "@/features/comparison-selection/components/comparison-builder";

vi.mock("@/features/address-search/api/address-suggestions", () => ({
  searchAddresses: vi.fn(),
}));

const mockedSearch = vi.mocked(searchAddresses);

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
});
