import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import type { Property } from "../lib/types";
import PropertyCard from "./PropertyCard";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN ?? "";

const PORTLAND: [number, number] = [-122.6765, 45.5231];

interface Props {
  property: Property | null;
  busy: boolean;
  onSearch: (address: string) => void;
  onPin: (lat: number, lon: number) => void;
}

export default function MapPanel({ property, busy, onSearch, onPin }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const marker = useRef<mapboxgl.Marker | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!container.current || map.current) return;
    const m = new mapboxgl.Map({
      container: container.current,
      style: "mapbox://styles/mapbox/standard",
      center: PORTLAND,
      zoom: 12,
      pitch: 45,
      bearing: -15,
    });
    map.current = m;
    m.on("click", (e) => onPin(e.lngLat.lat, e.lngLat.lng));
    m.on("style.load", () => {
      // 3D terrain for the colorful, tilted city view.
      if (!m.getSource("mapbox-dem")) {
        m.addSource("mapbox-dem", {
          type: "raster-dem",
          url: "mapbox://mapbox.mapbox-terrain-dem-v1",
          tileSize: 512,
          maxzoom: 14,
        });
      }
      m.setTerrain({ source: "mapbox-dem", exaggeration: 1.5 });
    });
    m.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "bottom-right");
  }, [onPin]);

  useEffect(() => {
    if (!map.current || !property || property.error) return;
    const lngLat: [number, number] = [property.lon, property.lat];
    if (!marker.current) {
      marker.current = new mapboxgl.Marker({ color: "#c14d28" });
    }
    marker.current.setLngLat(lngLat).addTo(map.current);
    map.current.flyTo({
      center: lngLat,
      zoom: 17,
      pitch: 60,
      bearing: 30,
      duration: 2500,
    });
  }, [property]);

  return (
    <div className="relative h-full w-full">
      <div ref={container} className="h-full w-full" />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (query.trim()) onSearch(query.trim());
        }}
        className="absolute left-4 right-4 top-4 flex gap-2"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a Portland address…"
          className="flex-1 rounded-lg border border-ink/10 bg-paper/95 px-3.5 py-2.5 text-sm text-ink shadow-sm outline-none transition placeholder:text-ink/35 focus:border-civic"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg bg-civic px-4 py-2.5 text-sm font-semibold text-cream shadow-sm transition hover:bg-civic-dark disabled:opacity-50"
        >
          {busy ? "…" : "Find"}
        </button>
      </form>

      {property && (
        <div className="absolute bottom-4 left-4 right-4">
          <PropertyCard property={property} />
        </div>
      )}
      {!property && (
        <div className="absolute bottom-4 left-4 rounded-full bg-paper/90 px-3.5 py-1.5 text-xs text-ink/50 shadow-sm">
          Click the map or search to set a property
        </div>
      )}
    </div>
  );
}
