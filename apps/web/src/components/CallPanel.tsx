const STEPS = [
  "Call the number below from any phone.",
  "Ask your permit, zoning, or building-code question out loud.",
  "The assistant looks up Portland city code and answers you by voice.",
];

export default function CallPanel() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8 p-8 text-center">
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-civic">
          Call the assistant
        </div>
        <a
          href="tel:+19342215222"
          className="mt-3 block font-display text-4xl font-semibold tracking-tight text-ink transition hover:text-civic"
        >
          (934) 221-5222
        </a>
        <p className="mt-2 text-sm text-ink/50">
          For residents who'd rather talk than type.
        </p>
      </div>

      <div className="h-px w-16 bg-ink/10" />

      <ol className="max-w-sm space-y-4 text-left">
        {STEPS.map((s, i) => (
          <li key={i} className="flex gap-3.5 text-sm text-ink/70">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-civic/30 bg-civic/10 font-mono text-xs font-semibold text-civic">
              {i + 1}
            </span>
            <span className="pt-0.5">{s}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
