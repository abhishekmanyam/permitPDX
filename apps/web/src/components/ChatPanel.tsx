import { useEffect, useRef, useState } from "react";
import { streamChat } from "../lib/api";
import type { ChatMessage, Property } from "../lib/types";
import MessageBubble from "./MessageBubble";

const SUGGESTIONS = [
  "How tall can my backyard fence be?",
  "Do I need a permit to build a deck?",
  "Can I build an ADU on my lot?",
  "What are the rules for a new sign on my shop?",
];

export default function ChatPanel({ property }: { property: Property | null }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const sessionId = useRef(crypto.randomUUID());
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [
      ...m,
      { role: "user", text },
      { role: "assistant", text: "", streaming: true },
    ]);

    try {
      for await (const ev of streamChat(text, sessionId.current, property)) {
        setMessages((m) => {
          const next = [...m];
          const last = next[next.length - 1];
          if (ev.type === "meta") {
            last.sources = ev.sources;
            last.risk = ev.risk;
            last.classification = ev.classification;
            last.status = undefined;
          } else if (ev.type === "status") {
            last.status = ev.text;
          } else if (ev.type === "token") {
            last.text += ev.text;
            last.status = undefined;
          } else if (ev.type === "error") {
            last.text = `Sorry — something went wrong: ${ev.message}`;
          } else if (ev.type === "done") {
            last.streaming = false;
          }
          return next;
        });
      }
    } catch (e) {
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1].text = `Sorry — connection error: ${String(e)}`;
        return next;
      });
    } finally {
      setBusy(false);
      setMessages((m) => {
        const next = [...m];
        if (next.length) next[next.length - 1].streaming = false;
        return next;
      });
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scroller} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="pt-6 text-center">
            <p className="text-sm text-gray-500">
              Ask about Portland permits, zoning, and building codes.
            </p>
            <div className="mt-4 flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 hover:border-civic hover:text-civic"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} msg={m} />
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2 border-t border-gray-200 bg-white p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-civic"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg bg-civic px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
