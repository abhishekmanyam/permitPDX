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

  // Smooth streaming: tokens land in `target`; a rAF loop reveals the
  // displayed text at a steady, rate-capped pace so bursty network
  // delivery always renders as a fluid typewriter, never a batch dump.
  const target = useRef("");
  const raf = useRef<number | null>(null);
  const lastTs = useRef(0);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight });
  }, [messages]);

  function patchLast(fn: (m: ChatMessage) => void) {
    setMessages((m) => {
      if (!m.length) return m;
      const next = [...m];
      next[next.length - 1] = { ...next[next.length - 1] };
      fn(next[next.length - 1]);
      return next;
    });
  }

  function startReveal() {
    if (raf.current != null) return;
    lastTs.current = performance.now();
    const tick = (now: number) => {
      const dt = Math.min(0.1, (now - lastTs.current) / 1000); // seconds
      lastTs.current = now;
      let keepGoing = false;
      setMessages((m) => {
        if (!m.length) return m;
        const next = [...m];
        const last = { ...next[next.length - 1] };
        const full = target.current;
        const shown = last.text.length;
        if (shown < full.length) {
          const gap = full.length - shown;
          // Steady chars/sec, nudged up by backlog but hard-capped so even a
          // huge burst reveals over ~1s rather than appearing all at once.
          const cps = last.streaming
            ? Math.min(620, Math.max(140, gap * 1.6))
            : Math.min(1300, Math.max(480, gap * 2.4));
          const add = Math.max(1, Math.round(cps * dt));
          last.text = full.slice(0, shown + add);
          next[next.length - 1] = last;
          keepGoing = true;
        } else if (last.streaming) {
          keepGoing = true; // caught up — wait for more tokens
        }
        return next;
      });
      raf.current = keepGoing ? requestAnimationFrame(tick) : null;
    };
    raf.current = requestAnimationFrame(tick);
  }

  useEffect(() => () => {
    if (raf.current != null) cancelAnimationFrame(raf.current);
  }, []);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setInput("");
    setBusy(true);
    target.current = "";
    setMessages((m) => [
      ...m,
      { role: "user", text },
      { role: "assistant", text: "", streaming: true },
    ]);

    try {
      for await (const ev of streamChat(text, sessionId.current, property)) {
        if (ev.type === "meta") {
          patchLast((l) => {
            l.sources = ev.sources;
            l.risk = ev.risk;
            l.classification = ev.classification;
            l.status = undefined;
          });
        } else if (ev.type === "status") {
          patchLast((l) => {
            l.status = ev.text;
          });
        } else if (ev.type === "token") {
          target.current += ev.text;
          startReveal();
        } else if (ev.type === "error") {
          target.current = `Sorry — something went wrong: ${ev.message}`;
          startReveal();
        }
      }
    } catch (e) {
      target.current = `Sorry — connection error: ${String(e)}`;
      startReveal();
    } finally {
      patchLast((l) => {
        l.streaming = false;
      });
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scroller} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="pt-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-civic/10 text-2xl">
              🏛️
            </div>
            <p className="text-sm font-medium text-gray-700">
              Ask about Portland permits, zoning &amp; building codes
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Every answer is cited to Portland City Code.
            </p>
            <div className="mt-5 flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-xl border border-gray-200 bg-white px-3.5 py-2.5 text-left text-sm text-gray-700 transition hover:border-civic hover:bg-civic/5 hover:text-civic"
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
          className="flex-1 rounded-xl border border-gray-200 px-3.5 py-2.5 text-sm outline-none transition focus:border-civic focus:ring-2 focus:ring-civic/15"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-civic px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-civic/90 disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
