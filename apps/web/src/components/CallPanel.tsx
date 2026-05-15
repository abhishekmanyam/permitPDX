const STEPS = [
  "Call the number below from any phone.",
  "Ask your permit, zoning, or building-code question out loud.",
  "The assistant looks up Portland city code and answers you by voice.",
];

export default function CallPanel() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 p-8 text-center">
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-civic">
          Call the assistant
        </div>
        <a
          href="tel:+19342215222"
          className="mt-2 block text-3xl font-bold text-gray-900"
        >
          (934) 221-5222
        </a>
        <p className="mt-1 text-sm text-gray-500">
          For residents who'd rather talk than type.
        </p>
      </div>
      <ol className="max-w-sm space-y-3 text-left">
        {STEPS.map((s, i) => (
          <li key={i} className="flex gap-3 text-sm text-gray-700">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-civic text-xs font-bold text-white">
              {i + 1}
            </span>
            {s}
          </li>
        ))}
      </ol>
    </div>
  );
}
