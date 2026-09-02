"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { AddressSuggestion } from "@/features/address-search/model/address-suggestion";
import {
  listFavourites,
  removeFavourite,
  resolveFavourite,
  saveFavourite,
  type Favourite,
} from "@/features/favourites/api/favourites";

export function useFavourites(onNotice: (notice: string) => void) {
  const queryClient = useQueryClient();
  const session = useQuery({
    queryFn: async () => {
      const response = await fetch("/api/auth/session", { cache: "no-store" });
      return (await response.json()) as {
        available?: boolean;
        authenticated?: boolean;
      };
    },
    queryKey: ["account-session"],
    retry: false,
  });
  const authenticated = session.data?.authenticated === true;
  const favourites = useQuery({
    enabled: authenticated,
    queryFn: listFavourites,
    queryKey: ["favourites"],
    retry: false,
  });
  const save = useMutation({
    mutationFn: saveFavourite,
    onError: () => onNotice("The favourite could not be saved. Try again."),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["favourites"] });
      onNotice("Address saved as a favourite. Official facts were not stored.");
    },
  });
  const remove = useMutation({
    mutationFn: removeFavourite,
    onError: () => onNotice("The favourite could not be removed. Try again."),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["favourites"] });
      onNotice("Favourite removed.");
    },
  });
  return {
    authenticated,
    available: session.data?.available !== false,
    favourites: favourites.data ?? [],
    loading: session.isPending || favourites.isPending,
    remove: remove.mutate,
    save: (addressId: string) => {
      if (!authenticated) {
        onNotice(
          "Sign in only if you want to save this address. Comparing remains account-free.",
        );
        return;
      }
      save.mutate(addressId);
    },
  };
}

export function FavouritesPanel({
  authenticated,
  available,
  favourites,
  loading,
  onAdd,
  onRemove,
}: Readonly<{
  authenticated: boolean;
  available: boolean;
  favourites: readonly Favourite[];
  loading: boolean;
  onAdd: (suggestion: AddressSuggestion) => void;
  onRemove: (id: string) => void;
}>) {
  if (!available) return null;
  if (!authenticated) {
    return (
      <div className="mt-5 rounded-xl border border-border bg-surface p-4 text-sm text-muted">
        <a
          className="font-semibold text-accent"
          href="/api/auth/login?return_to=%2F%23compare"
        >
          Sign in
        </a>{" "}
        to save address references. Search and comparison stay available without an
        account.
      </div>
    );
  }
  return (
    <section
      aria-labelledby="favourites-title"
      className="mt-5 rounded-xl border border-border bg-surface p-4"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="font-semibold" id="favourites-title">
          Your favourites
        </h2>
        <span className="text-xs text-muted">References only</span>
      </div>
      {loading ? <p className="mt-3 text-sm text-muted">Loading favourites…</p> : null}
      {!loading && favourites.length === 0 ? (
        <p className="mt-3 text-sm text-muted">
          No saved addresses yet. Use Save beside a selected home.
        </p>
      ) : null}
      <ul className="mt-3 space-y-2">
        {favourites.map((favourite) => (
          <FavouriteItem
            favourite={favourite}
            key={favourite.id}
            onAdd={onAdd}
            onRemove={onRemove}
          />
        ))}
      </ul>
    </section>
  );
}

function FavouriteItem({
  favourite,
  onAdd,
  onRemove,
}: Readonly<{
  favourite: Favourite;
  onAdd: (suggestion: AddressSuggestion) => void;
  onRemove: (id: string) => void;
}>) {
  const address = useQuery({
    queryFn: () => resolveFavourite(favourite.id),
    queryKey: ["favourite-address", favourite.id],
    retry: false,
  });
  return (
    <li className="flex flex-wrap items-center gap-2 rounded-lg bg-page p-3 text-sm">
      <span className="min-w-48 flex-1">
        {address.isPending
          ? "Resolving current address…"
          : address.isError
            ? "Address is no longer available"
            : address.data.displayName}
      </span>
      <button
        className="min-h-10 rounded-lg px-3 font-semibold text-accent hover:bg-accent-soft disabled:opacity-50"
        disabled={!address.data}
        onClick={() => address.data && onAdd(address.data)}
        type="button"
      >
        Add
      </button>
      <button
        aria-label="Remove favourite"
        className="min-h-10 rounded-lg px-3 text-muted hover:bg-accent-soft"
        onClick={() => onRemove(favourite.id)}
        type="button"
      >
        Remove
      </button>
    </li>
  );
}
