import {
  Children,
  createElement,
  isValidElement,
  useState,
  type ReactNode,
} from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import type { ChatMessage } from "../lib/types";
import RiskBadge from "./RiskBadge";

/**
 * While streaming, the text may end mid-markup (e.g. an unclosed `**`).
 * Drop the dangling marker so it doesn't flash as a literal `**`/`` ` ``
 * until its closing pair arrives.
 */
function tidyPartial(text: string): string {
  let t = text;
  for (const mark of ["**", "`"]) {
    const count = t.split(mark).length - 1;
    if (count % 2) {
      const i = t.lastIndexOf(mark);
      t = t.slice(0, i) + t.slice(i + mark.length);
    }
  }
  return t;
}

/**
 * Wrap every word of a markdown node's text in a blur-in span. Words are
 * keyed by index, so words already on screen keep their identity and never
 * re-animate — only newly streamed words fade in.
 */
function blurWords(children: ReactNode): ReactNode {
  return Children.map(children, (child) => {
    if (typeof child === "string") {
      return (child.match(/\S+\s*|\s+/g) ?? []).map((w, i) => (
        <span key={i} className="blur-word">
          {w}
        </span>
      ));
    }
    if (isValidElement(child)) return child; // nested element handles itself
    return child;
  });
}

// Markdown elements whose text should animate in, word by word.
const ANIMATED_TAGS = ["p", "li", "h1", "h2", "h3", "strong", "em", "blockquote"];
const animatedComponents: Components = Object.fromEntries(
  ANIMATED_TAGS.map((tag) => [
    tag,
    ({ children, node: _node, ...props }: { children?: ReactNode; node?: unknown }) =>
      createElement(tag, props, blurWords(children)),
  ]),
);

export default function MessageBubble({ msg }: { msg: ChatMessage }) {
  const [showSources, setShowSources] = useState(false);

  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-civic px-4 py-2.5 text-[15px] text-white shadow-sm">
          {msg.text}
        </div>
      </div>
    );
  }

  const streaming = msg.streaming;
  const empty = !msg.text;
  // Always tidy — a message can also end on an unclosed marker if the
  // stream was cut short, not just mid-token while streaming.
  const body = tidyPartial(msg.text);

  return (
    <div className="flex justify-start">
      <div className="max-w-[92%] rounded-2xl rounded-bl-md bg-white px-4 py-3 shadow-sm ring-1 ring-gray-100">
        {empty ? (
          <span className="flex items-center gap-2 text-sm text-gray-400">
            <span className="flex gap-1">
              <Dot /> <Dot delay="0.15s" /> <Dot delay="0.3s" />
            </span>
            {msg.status ?? "Thinking…"}
          </span>
        ) : (
          <div
            className={`answer text-[15px] leading-relaxed text-gray-800 ${
              streaming ? "is-streaming" : ""
            }`}
          >
            <ReactMarkdown components={streaming ? animatedComponents : undefined}>
              {body}
            </ReactMarkdown>
          </div>
        )}

        {msg.risk && <RiskBadge risk={msg.risk} />}

        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-3 border-t border-gray-100 pt-2">
            <button
              onClick={() => setShowSources((s) => !s)}
              className="text-xs font-semibold text-civic hover:underline"
            >
              {showSources ? "Hide" : "Show"} {msg.sources.length} cited sources
            </button>
            {showSources && (
              <ul className="mt-2 space-y-1">
                {msg.sources.map((s) => (
                  <li key={s.n} className="flex gap-2 text-xs text-gray-600">
                    <span className="font-bold text-gold">[{s.n}]</span>
                    <span>{s.title}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Dot({ delay = "0s" }: { delay?: string }) {
  return (
    <span
      className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-civic"
      style={{ animationDelay: delay }}
    />
  );
}
