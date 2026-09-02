"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

import type {
  LiveComparison,
  SpatialCoordinates,
} from "@/features/live-comparison/model/live-comparison";

export type SpatialMapPoint = Readonly<{
  coordinates: SpatialCoordinates;
  kind: "home" | "station";
  label: string;
  number: number;
}>;

const SpatialMap = dynamic(
  () =>
    import("@/features/map/components/spatial-map").then((module) => module.SpatialMap),
  {
    loading: () => (
      <div
        className="grid min-h-80 place-items-center bg-accent-soft p-8"
        role="status"
      >
        Loading optional map…
      </div>
    ),
    ssr: false,
  },
);

export function SpatialContext({
  comparison,
  labels,
}: Readonly<{
  comparison: LiveComparison;
  labels: ReadonlyMap<string, string>;
}>) {
  const [showMap, setShowMap] = useState(false);
  const homes: SpatialMapPoint[] = comparison.homes.flatMap((home, index) =>
    home.coordinates
      ? [
          {
            coordinates: home.coordinates,
            kind: "home" as const,
            label: `Home ${index + 1}: ${labels.get(home.addressId) ?? home.displayName ?? "selected official address"}`,
            number: index + 1,
          },
        ]
      : [],
  );
  const stations = new Map<string, SpatialMapPoint>();
  for (const [homeIndex, home] of comparison.homes.entries()) {
    for (const station of home.stations) {
      const key = `${station.id}:${station.coordinates.longitude}:${station.coordinates.latitude}`;
      stations.set(key, {
        coordinates: station.coordinates,
        kind: "station",
        label: `${station.name}, ${station.operator}, ${station.distanceKm} km from Home ${homeIndex + 1}`,
        number: homeIndex + 1,
      });
    }
  }
  const points = [...homes, ...stations.values()];

  return (
    <section
      aria-labelledby="spatial-context-title"
      className="mt-8"
      id="spatial-context"
    >
      <div className="rounded-xl border border-border bg-surface p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
          Optional supporting context
        </p>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-semibold" id="spatial-context-title">
              Spatial context
            </h3>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              Numbered homes and nearby monitoring stations from this live comparison.
              The map does not rank locations or measure conditions at a home.
            </p>
          </div>
          {points.length > 0 ? (
            <button
              aria-expanded={showMap}
              className="min-h-11 rounded-lg border border-border px-4 text-sm font-semibold hover:bg-accent-soft"
              onClick={() => setShowMap((visible) => !visible)}
              type="button"
            >
              {showMap ? "Hide interactive map" : "Show interactive map"}
            </button>
          ) : null}
        </div>

        {points.length === 0 ? (
          <p className="mt-5 text-sm text-muted">
            No coordinate evidence is available for this comparison.
          </p>
        ) : (
          <>
            {showMap ? (
              <div className="mt-5 overflow-hidden rounded-lg border border-border">
                <SpatialMap points={points} />
              </div>
            ) : null}
            <div className="mt-5 grid gap-5 md:grid-cols-2">
              <div>
                <h4 className="font-semibold">Selected homes</h4>
                <ol className="mt-2 space-y-2 text-sm text-muted">
                  {homes.map((home) => (
                    <li key={home.label}>{home.label}</li>
                  ))}
                </ol>
              </div>
              <div>
                <h4 className="font-semibold">Monitoring stations</h4>
                {stations.size === 0 ? (
                  <p className="mt-2 text-sm text-muted">
                    No station coordinates are available.
                  </p>
                ) : (
                  <ul className="mt-2 space-y-2 text-sm text-muted">
                    {[...stations.values()].map((station) => (
                      <li key={station.label}>{station.label}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            <p className="mt-5 text-xs leading-5 text-muted">
              Map © OpenFreeMap · © OpenMapTiles · data © OpenStreetMap contributors.
              Opening the map sends ordinary browser requests to OpenFreeMap; WoonLens
              does not persist map state or coordinates.
            </p>
          </>
        )}
      </div>
    </section>
  );
}
