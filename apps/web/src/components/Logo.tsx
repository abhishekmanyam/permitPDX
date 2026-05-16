/**
 * PermitPDX mark — a minimalist civic archway. Pure SVG, no emoji.
 */
export default function Logo({
  size = 36,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-[10px] bg-civic ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        width={size * 0.56}
        height={size * 0.56}
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden
      >
        <path
          d="M4 22V11.5a8 8 0 0 1 16 0V22"
          stroke="#f8f1e4"
          strokeWidth="2.3"
          strokeLinecap="round"
        />
        <path
          d="M12 22v-8.5"
          stroke="#f8f1e4"
          strokeWidth="2.3"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
