import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../lib/types";
import RiskBadge from "./RiskBadge";

export default function MessageBubble({ msg }: { msg: ChatMessage }) {
  const [showSources, setShowSources] = useState(false);

  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-civic px-4 py-2 text-white">
          {msg.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[92%] rounded-2xl rounded-bl-sm bg-white px-4 py-3 shadow">
        <div className="answer text-[15px] text-gray-800">
          {msg.text ? (
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          ) : (
            <span className="text-gray-400">Thinking…</span>
          )}
        </div>

        {msg.risk && <RiskBadge risk={msg.risk} />}

        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-3 border-t border-gray-100 pt-2">
            <button
              onClick={() => setShowSources((s) => !s)}
              className="text-xs font-semibold text-civic hover:underline"
            >
              {showSources ? "Hide" : "Show"} {msg.sources.length} sources
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
