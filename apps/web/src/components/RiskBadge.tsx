import type { Risk } from "../lib/types";

export default function RiskBadge({ risk }: { risk: Risk }) {
  if (risk.level === "LOW") return null;
  const high = risk.level === "HIGH";
  return (
    <div
      className="mt-3 flex gap-3 rounded-md p-3 text-sm"
      style={{
        background: high ? "#fdf0ed" : "#fdf8ee",
        borderLeft: `4px solid ${high ? "#c0492b" : "#d4a853"}`,
      }}
    >
      <span className="text-lg leading-none">{high ? "⚠️" : "💡"}</span>
      <div>
        <div className="font-bold" style={{ color: high ? "#9a2f1a" : "#8a6a1e" }}>
          {high ? "Heads up — consult a licensed professional" : "Worth a closer look"}
        </div>
        <div className="text-gray-700">{risk.reason}</div>
      </div>
    </div>
  );
}
