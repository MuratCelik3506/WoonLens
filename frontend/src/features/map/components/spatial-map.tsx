"use client";

import { useEffect, useRef, useState } from "react";
import {
  LngLatBounds,
  Map,
  Marker,
  NavigationControl,
  setWorkerUrl,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import type { SpatialMapPoint } from "@/features/map/components/spatial-context";

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const STYLE_URL = "https://tiles.openfreemap.org/styles/positron";

function markerElement(point: SpatialMapPoint): HTMLDivElement {
  const element = document.createElement("div");
  element.className =
    point.kind === "home"
      ? "grid size-9 place-items-center rounded-full border-2 border-surface bg-accent text-sm font-bold text-surface shadow-lg dark:text-page"
      : "size-4 rounded-sm border-2 border-surface bg-ink shadow-lg";
  element.textContent = point.kind === "home" ? point.number.toString() : "";
  element.setAttribute("aria-label", point.label);
  element.setAttribute("role", "img");
  return element;
}

export function SpatialMap({
  points,
}: Readonly<{ points: readonly SpatialMapPoint[] }>) {
  const container = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!container.current || points.length === 0) return;
    let map: Map | null = null;
    let active = true;
    const reportFailure = () => {
      if (active) setFailed(true);
    };
    try {
      map = new Map({
        attributionControl: {},
        container: container.current,
        cooperativeGestures: true,
        style: STYLE_URL,
      });
      map.addControl(new NavigationControl({ showCompass: false }), "top-right");
      const bounds = new LngLatBounds();
      for (const point of points) {
        const location: [number, number] = [
          point.coordinates.longitude,
          point.coordinates.latitude,
        ];
        bounds.extend(location);
        new Marker({ element: markerElement(point) }).setLngLat(location).addTo(map);
      }
      map.once("load", () => {
        map?.fitBounds(bounds, { duration: 0, maxZoom: 15, padding: 56 });
      });
      map.once("error", reportFailure);
    } catch {
      queueMicrotask(reportFailure);
    }
    return () => {
      active = false;
      map?.remove();
    };
  }, [points]);

  if (failed) {
    return (
      <div
        className="grid min-h-80 place-items-center bg-accent-soft p-8 text-center"
        role="status"
      >
        <p className="max-w-md text-sm leading-6">
          The interactive map is unavailable. The complete spatial context remains in
          the text list below.
        </p>
      </div>
    );
  }

  return (
    <div
      aria-label="Interactive spatial context map"
      className="h-96 w-full"
      ref={container}
    />
  );
}
