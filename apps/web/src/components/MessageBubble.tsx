import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../lib/types";
import RiskBadge from "./RiskBadge";

/**
 * While streaming, the text may end mid-markup (e.g. an unclosed `**`).
 * Trim a dangling marker so it doesn't flash as a literal `**`/`*`/`` ` ``
 * until its closing pair arrives.
 */
function tidyPartial(text: string): string {
  let t = text;
  if ((t.match(/\*\*/g)?.length ?? 0) % 2) t = t.replace(/\*\*(?!.*\*\*)/, "");
  if ((t.match(/`/g)?.length ?? 0) % 2) t = t.replace(/`(?!.*`)/, "");
  return t;
}

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
  const body = streaming ? tidyPartial(msg.text) : msg.text;

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
            <ReactMarkdown>{body}</ReactMarkdown>
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
