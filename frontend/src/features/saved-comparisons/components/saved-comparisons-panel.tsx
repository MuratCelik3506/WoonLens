"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { AddressSuggestion } from "@/features/address-search/model/address-suggestion";
import {
  createSavedComparison,
  deleteSavedComparison,
  listSavedComparisons,
  renameSavedComparison,
  resolveSavedAddresses,
  type SavedComparison,
} from "@/features/saved-comparisons/api/saved-comparisons";

export function SavedComparisonsPanel({
  authenticated,
  selectedIds,
  onOpen,
  onNotice,
}: Readonly<{
  authenticated: boolean;
  selectedIds: readonly string[];
  onOpen: (addresses: readonly AddressSuggestion[]) => void;
  onNotice: (notice: string) => void;
}>) {
  const [name, setName] = useState("");
  const client = useQueryClient();
  const query = useQuery({
    enabled: authenticated,
    queryFn: listSavedComparisons,
    queryKey: ["saved-comparisons"],
    retry: false,
  });
  const create = useMutation({
    mutationFn: createSavedComparison,
    onSuccess: (created) => {
      client.setQueryData<readonly SavedComparison[]>(
        ["saved-comparisons"],
        (current = []) => [created, ...current],
      );
      setName("");
      onNotice("Comparison list saved. Official facts were not stored.");
    },
  });
  const remove = useMutation({
    mutationFn: deleteSavedComparison,
    onSuccess: (id) =>
      client.setQueryData<readonly SavedComparison[]>(
        ["saved-comparisons"],
        (current = []) => current.filter((item) => item.id !== id),
      ),
  });
  const rename = useMutation({
    mutationFn: renameSavedComparison,
    onSuccess: (updated) =>
      client.setQueryData<readonly SavedComparison[]>(
        ["saved-comparisons"],
        (current = []) =>
          current.map((item) => (item.id === updated.id ? updated : item)),
      ),
  });
  const open = useMutation({
    mutationFn: resolveSavedAddresses,
    onError: () => onNotice("One or more saved addresses are no longer available."),
    onSuccess: onOpen,
  });

  if (!authenticated) return null;
  return (
    <section
      aria-labelledby="saved-comparisons-title"
      className="mt-5 rounded-xl border border-border bg-surface p-4"
    >
      <h2 className="font-semibold" id="saved-comparisons-title">
        Saved comparisons
      </h2>
      <form
        className="mt-3 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          create.mutate({ name, addressIds: selectedIds });
        }}
      >
        <input
          aria-label="Comparison name"
          className="min-h-11 min-w-48 flex-1 rounded-lg border border-border bg-page px-3"
          maxLength={80}
          onChange={(event) => setName(event.target.value)}
          placeholder="e.g. Rotterdam shortlist"
          value={name}
        />
        <button
          className="min-h-11 rounded-lg bg-accent px-4 font-semibold text-surface disabled:opacity-50 dark:text-page"
          disabled={
            selectedIds.length < 2 ||
            selectedIds.length > 5 ||
            !name.trim() ||
            create.isPending
          }
          type="submit"
        >
          Save list
        </button>
      </form>
      {query.isPending ? (
        <p className="mt-3 text-sm text-muted">Loading saved comparisons…</p>
      ) : null}
      <ul className="mt-3 space-y-2">
        {(query.data ?? []).map((item) => (
          <SavedItem
            item={item}
            key={item.id}
            onDelete={() => remove.mutate(item.id)}
            onOpen={() => open.mutate(item.addressIds)}
            onRename={(nextName) => rename.mutate({ id: item.id, name: nextName })}
          />
        ))}
      </ul>
    </section>
  );
}

function SavedItem({
  item,
  onDelete,
  onOpen,
  onRename,
}: Readonly<{
  item: SavedComparison;
  onDelete: () => void;
  onOpen: () => void;
  onRename: (name: string) => void;
}>) {
  const [name, setName] = useState(item.name);
  return (
    <li className="rounded-lg bg-page p-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          aria-label={`Name for ${item.name}`}
          className="min-h-10 min-w-40 flex-1 rounded-lg border border-border bg-surface px-3 text-sm"
          maxLength={80}
          onChange={(event) => setName(event.target.value)}
          value={name}
        />
        <span className="text-xs text-muted">{item.addressIds.length} homes</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          className="min-h-10 rounded-lg px-3 font-semibold text-accent hover:bg-accent-soft"
          onClick={onOpen}
          type="button"
        >
          Open
        </button>
        <button
          className="min-h-10 rounded-lg px-3 text-sm hover:bg-accent-soft disabled:opacity-50"
          disabled={!name.trim() || name.trim() === item.name}
          onClick={() => onRename(name)}
          type="button"
        >
          Rename
        </button>
        <button
          className="min-h-10 rounded-lg px-3 text-sm text-muted hover:bg-accent-soft"
          onClick={onDelete}
          type="button"
        >
          Delete
        </button>
      </div>
    </li>
  );
}
