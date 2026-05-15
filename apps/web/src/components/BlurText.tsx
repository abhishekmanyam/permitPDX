/**
 * Renders streaming text word-by-word with a Claude-style blur-in reveal.
 * Each word is keyed by index, so words already on screen keep their
 * identity and never re-animate — only newly arrived words fade in.
 */
export default function BlurText({ text }: { text: string }) {
  // Keep trailing whitespace attached to each word so spacing is preserved.
  const words = text.match(/\S+\s*|\s+/g) ?? [];
  return (
    <>
      {words.map((w, i) => (
        <span key={i} className="blur-word">
          {w}
        </span>
      ))}
    </>
  );
}
