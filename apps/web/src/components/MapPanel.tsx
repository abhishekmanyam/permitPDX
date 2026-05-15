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
    map.current = new mapboxgl.Map({
      container: container.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: PORTLAND,
      zoom: 11,
    });
    map.current.on("click", (e) => onPin(e.lngLat.lat, e.lngLat.lng));
  }, [onPin]);

  useEffect(() => {
    if (!map.current || !property || property.error) return;
    const lngLat: [number, number] = [property.lon, property.lat];
    if (!marker.current) {
      marker.current = new mapboxgl.Marker({ color: "#1a5632" });
    }
    marker.current.setLngLat(lngLat).addTo(map.current);
    map.current.flyTo({ center: lngLat, zoom: 16, speed: 1.4 });
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
          className="flex-1 rounded-lg border border-gray-200 bg-white/95 px-3 py-2 text-sm shadow outline-none focus:border-civic"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg bg-civic px-4 py-2 text-sm font-semibold text-white shadow disabled:opacity-50"
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
        <div className="absolute bottom-4 left-4 rounded-md bg-white/90 px-3 py-1.5 text-xs text-gray-500 shadow">
          Click the map or search to set a property
        </div>
      )}
    </div>
  );
}
