import type { Property } from "../lib/types";

export default function PropertyCard({ property }: { property: Property }) {
  if (property.error) {
    return (
      <div className="rounded-xl bg-paper p-3.5 text-sm text-red-700 shadow-sm ring-1 ring-ink/8">
        {property.error}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl bg-paper shadow-[0_18px_44px_-18px_rgba(42,29,18,0.45)] ring-1 ring-ink/8">
      {/* address header */}
      <div className="border-b border-ink/8 bg-civic/6 px-4 py-3">
        <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-civic">
          <span className="h-1.5 w-1.5 rounded-full bg-civic" />
          Selected property
        </div>
        <div className="mt-1 font-sans text-[0.95rem] font-semibold leading-snug tracking-tight text-ink">
          {property.address}
        </div>
      </div>

      {/* zoning facts */}
      <dl className="grid grid-cols-2 gap-px bg-ink/8">
        <Field label="Zone" className="col-span-2">
          {property.zone ? (
            <span className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <span className="rounded-md bg-civic px-1.5 py-0.5 font-mono text-xs font-semibold text-cream">
                {property.zone}
              </span>
              {property.zone_desc && (
                <span className="text-ink/70">{property.zone_desc}</span>
              )}
            </span>
          ) : (
            <Muted>Not available</Muted>
          )}
        </Field>
        <Field label="Overlays">
          {property.overlays ? (
            property.overlays
          ) : (
            <Muted>None</Muted>
          )}
        </Field>
        <Field label="Comp plan">
          {property.comp_plan ?? <Muted>—</Muted>}
        </Field>
      </dl>
    </div>
  );
}

function Field({
  label,
  children,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-paper px-4 py-2.5 ${className}`}>
      <dt className="text-[10px] font-semibold uppercase tracking-[0.14em] text-ink/40">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm font-medium text-ink/85">{children}</dd>
    </div>
  );
}

function Muted({ children }: { children: React.ReactNode }) {
  return <span className="font-normal text-ink/40">{children}</span>;
}
