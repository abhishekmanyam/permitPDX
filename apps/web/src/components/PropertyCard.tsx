import type { Property } from "../lib/types";

export default function PropertyCard({ property }: { property: Property }) {
  if (property.error) {
    return (
      <div className="rounded-lg bg-white p-3 text-sm text-red-700 shadow">
        {property.error}
      </div>
    );
  }
  const rows: [string, string | undefined][] = [
    ["Zone", property.zone_desc ? `${property.zone} — ${property.zone_desc}` : property.zone],
    ["Overlays", property.overlays || "None"],
    ["Comp plan", property.comp_plan],
  ];
  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <div className="text-xs font-semibold uppercase tracking-wide text-civic">
        Property
      </div>
      <div className="mt-1 font-semibold text-gray-900">{property.address}</div>
      <dl className="mt-2 space-y-1 text-sm">
        {rows.map(([k, v]) =>
          v ? (
            <div key={k} className="flex gap-2">
              <dt className="w-24 shrink-0 text-gray-500">{k}</dt>
              <dd className="font-medium text-gray-800">{v}</dd>
            </div>
          ) : null,
        )}
      </dl>
    </div>
  );
}
