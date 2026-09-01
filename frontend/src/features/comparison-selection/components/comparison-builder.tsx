"use client";

import { useQuery } from "@tanstack/react-query";
import { useId, useRef, useState } from "react";

import { searchAddresses } from "@/features/address-search/api/address-suggestions";
import type { AddressSuggestion } from "@/features/address-search/model/address-suggestion";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";

const MINIMUM_HOMES = 2;
const MAXIMUM_HOMES = 5;

type SelectedHome = Readonly<{
  number: number;
  suggestion: AddressSuggestion;
}>;

export function ComparisonBuilder() {
  const [selectedHomes, setSelectedHomes] = useState<readonly SelectedHome[]>([]);
  const [notice, setNotice] = useState("");

  function addHome(suggestion: AddressSuggestion): boolean {
    if (selectedHomes.some((home) => home.suggestion.id === suggestion.id)) {
      setNotice(`${suggestion.displayName} is already selected.`);
      return false;
    }
    if (selectedHomes.length >= MAXIMUM_HOMES) {
      setNotice("Remove a home before adding another. You can compare up to five.");
      return false;
    }

    const usedNumbers = new Set(selectedHomes.map((home) => home.number));
    const number = [1, 2, 3, 4, 5].find((candidate) => !usedNumbers.has(candidate));
    if (number === undefined) return false;

    setSelectedHomes((homes) => [...homes, { number, suggestion }]);
    setNotice(`${suggestion.displayName} added to the comparison.`);
    return true;
  }

  function removeHome(id: string) {
    setSelectedHomes((homes) => homes.filter((home) => home.suggestion.id !== id));
    setNotice("Home removed from the comparison.");
  }

  return (
    <section
      className="mx-auto grid max-w-7xl gap-10 px-5 py-20 lg:grid-cols-[minmax(0,1fr)_20rem] lg:px-8 lg:py-28"
      id="compare"
    >
      <div className="max-w-3xl">
        <p className="mb-5 text-sm font-semibold uppercase tracking-[0.16em] text-accent">
          Official data. Clear differences.
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-[-0.04em] sm:text-5xl lg:text-6xl">
          Compare Dutch homes with trusted public data.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-muted">
          Search official addresses and build a comparison of two to five homes. No
          account is required and provider facts are not stored.
        </p>

        <AddressSearch
          disabled={selectedHomes.length >= MAXIMUM_HOMES}
          onSelect={addHome}
          selectedIds={new Set(selectedHomes.map((home) => home.suggestion.id))}
        />
        <p aria-live="polite" className="mt-4 min-h-6 text-sm text-muted">
          {notice}
        </p>
      </div>

      <ComparisonTray homes={selectedHomes} onRemove={removeHome} />
    </section>
  );
}

type AddressSearchProps = Readonly<{
  disabled: boolean;
  onSelect: (suggestion: AddressSuggestion) => boolean;
  selectedIds: ReadonlySet<string>;
}>;

function AddressSearch({ disabled, onSelect, selectedIds }: AddressSearchProps) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [hasFocus, setHasFocus] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();
  const normalizedQuery = query.trim();
  const debouncedQuery = useDebouncedValue(normalizedQuery, 300);
  const canSearch = debouncedQuery.length >= 2 && !disabled;
  const queryIsSettled = normalizedQuery === debouncedQuery;

  const suggestions = useQuery({
    enabled: canSearch,
    gcTime: 0,
    queryFn: ({ signal }) => searchAddresses(debouncedQuery, signal),
    queryKey: ["address-suggestions", debouncedQuery],
    retry: false,
  });

  const items = canSearch && queryIsSettled ? (suggestions.data?.items ?? []) : [];
  const listIsOpen = hasFocus && normalizedQuery.length >= 2 && !disabled;

  function choose(suggestion: AddressSuggestion) {
    if (onSelect(suggestion)) {
      setQuery("");
      setActiveIndex(-1);
    }
    inputRef.current?.focus();
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (!listIsOpen || items.length === 0) {
      if (event.key === "Escape") setHasFocus(false);
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => (index + 1) % items.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => (index <= 0 ? items.length - 1 : index - 1));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      choose(items[activeIndex]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setHasFocus(false);
      setActiveIndex(-1);
      inputRef.current?.blur();
    }
  }

  return (
    <div className="relative mt-9 rounded-xl border border-border bg-surface p-4 sm:p-5">
      <label className="block text-sm font-semibold" htmlFor="address-search">
        Find an official address
      </label>
      <input
        aria-activedescendant={
          activeIndex >= 0 ? `${listboxId}-option-${activeIndex}` : undefined
        }
        aria-autocomplete="list"
        aria-controls={listboxId}
        aria-expanded={listIsOpen}
        className="mt-3 min-h-12 w-full rounded-lg border border-border bg-page px-4 text-base placeholder:text-muted disabled:cursor-not-allowed disabled:opacity-60"
        disabled={disabled}
        id="address-search"
        onBlur={() => window.setTimeout(() => setHasFocus(false), 100)}
        onChange={(event) => {
          setQuery(event.target.value);
          setActiveIndex(-1);
        }}
        onFocus={() => setHasFocus(true)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Five homes selected" : "Start typing a Dutch address"}
        ref={inputRef}
        role="combobox"
        type="search"
        value={query}
      />
      <p className="mt-3 text-sm text-muted">
        {disabled
          ? "Remove a home to search again."
          : "Type at least two characters, then select an official suggestion."}
      </p>

      {listIsOpen ? (
        <div
          className="absolute inset-x-4 top-full z-20 mt-2 overflow-hidden rounded-xl border border-border bg-surface shadow-xl sm:inset-x-5"
          id={listboxId}
          role="listbox"
        >
          {!queryIsSettled || suggestions.isPending ? (
            <p aria-live="polite" className="p-4 text-sm text-muted">
              Searching official addresses…
            </p>
          ) : null}

          {queryIsSettled && suggestions.isError ? (
            <div className="flex flex-wrap items-center justify-between gap-3 p-4">
              <p className="text-sm text-muted">
                Address search is currently unavailable.
              </p>
              <button
                className="min-h-11 rounded-lg border border-border px-4 text-sm font-semibold hover:bg-accent-soft"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => void suggestions.refetch()}
                type="button"
              >
                Try again
              </button>
            </div>
          ) : null}

          {queryIsSettled && suggestions.isSuccess && items.length === 0 ? (
            <p className="p-4 text-sm text-muted">No official addresses found.</p>
          ) : null}

          {items.map((suggestion, index) => {
            const alreadySelected = selectedIds.has(suggestion.id);
            return (
              <button
                aria-disabled={alreadySelected}
                aria-selected={activeIndex === index}
                className="flex min-h-14 w-full items-start justify-between gap-4 border-b border-border px-4 py-3 text-left last:border-b-0 hover:bg-accent-soft aria-selected:bg-accent-soft"
                id={`${listboxId}-option-${index}`}
                key={suggestion.id}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => choose(suggestion)}
                role="option"
                type="button"
              >
                <span>
                  <span className="block font-medium">{suggestion.displayName}</span>
                  <span className="mt-1 block text-xs text-muted">
                    {suggestion.source.provider} · Official address
                  </span>
                </span>
                {alreadySelected ? (
                  <span className="text-xs font-semibold text-accent">Selected</span>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

function ComparisonTray({
  homes,
  onRemove,
}: Readonly<{
  homes: readonly SelectedHome[];
  onRemove: (id: string) => void;
}>) {
  const ready = homes.length >= MINIMUM_HOMES && homes.length <= MAXIMUM_HOMES;
  const [message, setMessage] = useState("");

  return (
    <aside className="sticky bottom-4 self-start rounded-xl border border-border bg-surface shadow-lg lg:top-6 lg:shadow-none">
      <details className="group" open>
        <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 lg:cursor-default">
          <h2 className="text-lg font-semibold">Selected homes</h2>
          <span className="text-sm text-muted">{homes.length} of 5</span>
        </summary>
        <div className="border-t border-border p-5 lg:block">
          {homes.length === 0 ? (
            <p className="text-sm leading-6 text-muted">
              Add at least two official addresses to begin a live comparison.
            </p>
          ) : (
            <ol className="space-y-3">
              {homes.map((home) => (
                <li className="flex items-start gap-3" key={home.suggestion.id}>
                  <span className="grid size-7 shrink-0 place-items-center rounded-full bg-accent text-sm font-semibold text-surface dark:text-page">
                    {home.number}
                  </span>
                  <span className="min-w-0 flex-1 text-sm leading-5">
                    {home.suggestion.displayName}
                  </span>
                  <button
                    aria-label={`Remove ${home.suggestion.displayName}`}
                    className="min-h-11 shrink-0 rounded-lg px-2 text-sm font-semibold text-accent hover:bg-accent-soft"
                    onClick={() => onRemove(home.suggestion.id)}
                    type="button"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ol>
          )}

          <button
            className="mt-6 min-h-12 w-full rounded-lg bg-accent px-5 font-semibold text-surface disabled:cursor-not-allowed disabled:opacity-60 dark:text-page"
            disabled={!ready}
            onClick={() =>
              setMessage("Live comparison results arrive in the next feature.")
            }
            type="button"
          >
            Compare homes
          </button>
          <p aria-live="polite" className="mt-3 min-h-5 text-xs text-muted">
            {message || (ready ? "Your selection is ready." : "Select 2–5 homes.")}
          </p>
        </div>
      </details>
    </aside>
  );
}
