import { afterEach, describe, expect, it, vi } from "vitest";

import {
  listFavourites,
  resolveFavourite,
  saveFavourite,
} from "@/features/favourites/api/favourites";

afterEach(() => vi.unstubAllGlobals());

describe("favourites API", () => {
  it("maps only minimum persisted reference fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            items: [
              {
                created_at: "2026-09-02T12:00:00Z",
                id: "favourite-id",
                pdok_address_id: "address-id",
              },
            ],
          }),
        ),
      ),
    );

    await expect(listFavourites()).resolves.toEqual([
      {
        createdAt: "2026-09-02T12:00:00Z",
        id: "favourite-id",
        pdokAddressId: "address-id",
      },
    ]);
  });

  it("sends only the opaque PDOK identifier when saving", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          created_at: "2026-09-02T12:00:00Z",
          id: "favourite-id",
          pdok_address_id: "address-id",
        }),
      ),
    );
    vi.stubGlobal("fetch", fetcher);

    await expect(saveFavourite("address-id")).resolves.toEqual({
      createdAt: "2026-09-02T12:00:00Z",
      id: "favourite-id",
      pdokAddressId: "address-id",
    });

    expect(JSON.parse(fetcher.mock.calls[0][1].body as string)).toEqual({
      pdok_address_id: "address-id",
    });
  });

  it("builds a transient display label from a live resolved address", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            city: "Den Haag",
            house_letter: null,
            house_number: "10",
            house_number_suffix: null,
            id: "address-id",
            postal_code: "1234AB",
            source: { dataset: "BAG", provider: "PDOK" },
            street: "Examplelaan",
          }),
        ),
      ),
    );

    await expect(resolveFavourite("favourite-id")).resolves.toMatchObject({
      displayName: "Examplelaan 10, 1234AB Den Haag",
      id: "address-id",
    });
  });
});
