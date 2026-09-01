export type AddressSuggestion = Readonly<{
  id: string;
  displayName: string;
  source: Readonly<{
    provider: string;
    dataset: string;
  }>;
}>;

export type AddressSuggestions = Readonly<{
  items: readonly AddressSuggestion[];
}>;

export function parseAddressSuggestions(value: unknown): AddressSuggestions {
  if (!isRecord(value) || !Array.isArray(value.items)) {
    throw new Error("Address suggestion response is invalid");
  }

  return {
    items: value.items.map((item) => {
      if (
        !isRecord(item) ||
        typeof item.id !== "string" ||
        typeof item.display_name !== "string" ||
        !isRecord(item.source) ||
        typeof item.source.provider !== "string" ||
        typeof item.source.dataset !== "string"
      ) {
        throw new Error("Address suggestion response is invalid");
      }

      return {
        id: item.id,
        displayName: item.display_name,
        source: {
          dataset: item.source.dataset,
          provider: item.source.provider,
        },
      };
    }),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
