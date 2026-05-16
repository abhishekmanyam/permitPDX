import Logo from "./Logo";

const FEATURES = [
  {
    no: "01",
    title: "Property-aware",
    body: "Search any Portland address and answers account for its zone, overlays and comp plan.",
  },
  {
    no: "02",
    title: "Cited to city code",
    body: "Every statement is traced to the exact Portland City Code section behind it.",
  },
  {
    no: "03",
    title: "Chat, avatar or call",
    body: "Type a question, speak with a live avatar, or phone in — whichever you prefer.",
  },
];

const SAMPLES = [
  "How tall can my backyard fence be?",
  "Do I need a permit to build a deck?",
  "Can I build an ADU on my lot?",
];

export default function Landing({ onEnter }: { onEnter: (q?: string) => void }) {
  return (
    <div className="min-h-full bg-cream text-ink">
      <div className="mx-auto flex min-h-full max-w-6xl flex-col px-6">
        {/* nav */}
        <header className="flex items-center justify-between py-6">
          <div className="flex items-center gap-3">
            <Logo size={38} />
            <div className="leading-tight">
              <div className="font-semibold tracking-tight">PermitPDX</div>
              <div className="text-[11px] uppercase tracking-[0.14em] text-ink/40">
                City of Portland
              </div>
            </div>
          </div>
          <button
            onClick={() => onEnter()}
            className="rounded-full border border-ink/15 px-5 py-2 text-sm font-medium text-ink/70 transition hover:border-civic hover:text-civic"
          >
            Open assistant
          </button>
        </header>

        {/* hero */}
        <main className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <div className="rise inline-flex items-center gap-2 rounded-full border border-civic/25 bg-civic/8 px-3.5 py-1.5 text-xs font-medium tracking-wide text-civic">
              <span className="h-1.5 w-1.5 rounded-full bg-civic" />
              Permits · Zoning · Building code
            </div>

            <h1
              className="rise mt-6 font-display text-[3.4rem] font-semibold leading-[1.02] tracking-tight sm:text-[4.6rem]"
              style={{ animationDelay: "0.05s" }}
            >
              Permit answers,
              <br />
              <span className="text-civic italic">without the runaround.</span>
            </h1>

            <p
              className="rise mt-6 max-w-md text-[1.05rem] leading-relaxed text-ink/60"
              style={{ animationDelay: "0.12s" }}
            >
              Ask anything about building, zoning and permits in Portland — and
              get a clear, plain-English answer, every claim cited to the city
              code.
            </p>

            <div
              className="rise mt-9 flex flex-wrap items-center gap-4"
              style={{ animationDelay: "0.18s" }}
            >
              <button
                onClick={() => onEnter()}
                className="rounded-full bg-civic px-7 py-3.5 text-sm font-semibold text-cream shadow-sm transition hover:-translate-y-0.5 hover:bg-civic-dark"
              >
                Launch the assistant
              </button>
              <span className="text-xs text-ink/40">
                Free · No sign-in required
              </span>
            </div>

            <div
              className="rise mt-10"
              style={{ animationDelay: "0.24s" }}
            >
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-ink/35">
                Start with a question
              </div>
              <div className="flex flex-wrap gap-2">
                {SAMPLES.map((q) => (
                  <button
                    key={q}
                    onClick={() => onEnter(q)}
                    className="rounded-full border border-ink/12 bg-paper px-4 py-2 text-sm text-ink/65 transition hover:border-civic hover:text-civic"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* product specimen */}
          <div
            className="rise relative"
            style={{ animationDelay: "0.3s" }}
          >
            <div className="absolute -inset-4 -z-10 rounded-[2rem] bg-civic/8" />
            <div className="overflow-hidden rounded-2xl border border-ink/10 bg-paper shadow-[0_24px_60px_-24px_rgba(42,29,18,0.35)]">
              <div className="flex items-center gap-2 border-b border-ink/8 px-5 py-3">
                <Logo size={22} />
                <span className="text-xs font-medium text-ink/50">
                  Portland Permit Assistant
                </span>
              </div>
              <div className="space-y-4 p-5">
                <div className="ml-auto w-fit max-w-[80%] rounded-2xl rounded-br-md bg-civic px-4 py-2.5 text-sm text-cream">
                  How tall can my backyard fence be?
                </div>
                <div className="max-w-[92%] rounded-2xl rounded-bl-md border border-ink/8 bg-cream px-4 py-3 text-sm leading-relaxed text-ink/80">
                  In most residential zones, a rear-yard fence may be up to{" "}
                  <span className="font-semibold text-ink">8 feet</span> tall.
                  Within the front setback the limit drops to{" "}
                  <span className="font-semibold text-ink">3½ feet</span>.
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    <span className="rounded-md bg-gold/15 px-2 py-0.5 font-mono text-[11px] text-gold">
                      PCC 33.110.255
                    </span>
                    <span className="rounded-md bg-civic/10 px-2 py-0.5 font-mono text-[11px] text-civic">
                      Zone R5
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* features */}
        <section className="grid gap-px overflow-hidden rounded-2xl border border-ink/10 bg-ink/10 sm:grid-cols-3">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className="rise bg-cream p-6"
              style={{ animationDelay: `${0.34 + i * 0.07}s` }}
            >
              <div className="font-mono text-xs tracking-widest text-civic">
                {f.no}
              </div>
              <div className="mt-3 font-display text-lg font-semibold">
                {f.title}
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-ink/55">
                {f.body}
              </p>
            </div>
          ))}
        </section>

        <footer className="mt-8 flex flex-col items-center gap-1 border-t border-ink/10 py-6 text-center">
          <div className="text-xs text-ink/40">
            PermitPDX — a faster way through Portland city code.
          </div>
          <div className="text-[11px] text-ink/30">
            Informational only. Not an official city determination.
          </div>
        </footer>
      </div>
    </div>
  );
}
