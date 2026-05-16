import { useEffect, useRef, useState } from "react";
import { streamChat } from "../lib/api";
import type { ChatMessage, Property } from "../lib/types";
import MessageBubble from "./MessageBubble";
import Logo from "./Logo";

const SUGGESTIONS = [
  "How tall can my backyard fence be?",
  "Do I need a permit to build a deck?",
  "Can I build an ADU on my lot?",
  "What are the rules for a new sign on my shop?",
];

export default function ChatPanel({
  property,
  initialQuestion,
}: {
  property: Property | null;
  initialQuestion?: string;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const sessionId = useRef(crypto.randomUUID());
  const scroller = useRef<HTMLDivElement>(null);

  // Smooth streaming: tokens land in `target`; a rAF loop reveals the
  // displayed text at a steady, rate-capped pace so bursty network
  // delivery always renders as a fluid typewriter, never a batch dump.
  // `shown` and `streamingRef` mirror reveal progress / stream state in
  // refs so the rAF loop can read them synchronously — React state
  // updaters run too late to decide whether the loop should continue.
  const target = useRef("");
  const shown = useRef(0);
  const streamingRef = useRef(false);
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
      const full = target.current;
      const have = shown.current;
      if (have < full.length) {
        const gap = full.length - have;
        // Steady chars/sec, nudged up by backlog but hard-capped so even a
        // huge burst reveals over ~1s rather than appearing all at once.
        const cps = streamingRef.current
          ? Math.min(620, Math.max(140, gap * 1.6))
          : Math.min(1300, Math.max(480, gap * 2.4));
        const add = Math.max(1, Math.round(cps * dt));
        shown.current = Math.min(full.length, have + add);
        patchLast((l) => {
          l.text = full.slice(0, shown.current);
        });
        raf.current = requestAnimationFrame(tick);
      } else if (streamingRef.current) {
        raf.current = requestAnimationFrame(tick); // caught up — wait for more
      } else {
        raf.current = null; // fully revealed and stream finished
      }
    };
    raf.current = requestAnimationFrame(tick);
  }

  useEffect(() => () => {
    if (raf.current != null) cancelAnimationFrame(raf.current);
  }, []);

  // Auto-send the question the user typed on the landing screen, once.
  const sentInitial = useRef(false);
  useEffect(() => {
    if (sentInitial.current || !initialQuestion?.trim()) return;
    sentInitial.current = true;
    send(initialQuestion);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setInput("");
    setBusy(true);
    target.current = "";
    shown.current = 0;
    streamingRef.current = true;
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
      // Stream is done — let the reveal loop drain the rest of `target`
      // and stop on its own. Re-kick in case it had already idled out.
      streamingRef.current = false;
      patchLast((l) => {
        l.streaming = false;
      });
      startReveal();
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scroller} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="pt-10">
            <Logo size={44} className="mb-4" />
            <h2 className="font-display text-xl font-semibold text-ink">
              Ask about Portland permits, zoning &amp; building code
            </h2>
            <p className="mt-1.5 text-sm text-ink/50">
              Every answer is traced to a Portland City Code section.
            </p>
            <div className="mt-6 flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="group flex items-center justify-between rounded-xl border border-ink/10 bg-paper px-4 py-3 text-left text-sm text-ink/70 transition hover:border-civic hover:text-civic"
                >
                  {s}
                  <span className="text-ink/25 transition group-hover:translate-x-0.5 group-hover:text-civic">
                    →
                  </span>
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
        className="flex gap-2 border-t border-ink/10 bg-paper p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="flex-1 rounded-xl border border-ink/12 bg-cream px-3.5 py-2.5 text-sm text-ink outline-none transition placeholder:text-ink/35 focus:border-civic focus:ring-2 focus:ring-civic/15"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-civic px-5 py-2.5 text-sm font-semibold text-cream transition hover:bg-civic-dark disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
