import { useCallback, useState } from "react";
import MapPanel from "./components/MapPanel";
import ChatPanel from "./components/ChatPanel";
import AvatarPanel from "./components/AvatarPanel";
import CallPanel from "./components/CallPanel";
import { resolveAddress, reverseGeocode } from "./lib/api";
import type { Property } from "./lib/types";

type Tab = "chat" | "avatar" | "call";

const TABS: { id: Tab; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "avatar", label: "Avatar" },
  { id: "call", label: "Call" },
];

export default function App() {
  const [property, setProperty] = useState<Property | null>(null);
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<Tab>("chat");

  const onSearch = useCallback(async (address: string) => {
    setBusy(true);
    try {
      setProperty(await resolveAddress(address));
    } finally {
      setBusy(false);
    }
  }, []);

  const onPin = useCallback(async (lat: number, lon: number) => {
    setBusy(true);
    try {
      setProperty(await reverseGeocode(lat, lon));
    } finally {
      setBusy(false);
    }
  }, []);

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-civic text-white">
            ▣
          </span>
          <div>
            <div className="font-bold leading-tight text-gray-900">
              Portland Permit Assistant
            </div>
            <div className="text-xs text-gray-500">
              City code, zoning &amp; permits — with cited answers
            </div>
          </div>
        </div>
        <span className="hidden text-xs text-gray-400 sm:block">
          Informational only — not an official determination
        </span>
      </header>

      <main className="flex min-h-0 flex-1 flex-col md:flex-row">
        <section className="h-64 md:h-auto md:w-1/2">
          <MapPanel
            property={property}
            busy={busy}
            onSearch={onSearch}
            onPin={onPin}
          />
        </section>

        <section className="flex min-h-0 flex-1 flex-col border-l border-gray-200 bg-cream md:w-1/2">
          <nav className="flex gap-1 border-b border-gray-200 bg-white px-3">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`border-b-2 px-4 py-2.5 text-sm font-semibold ${
                  tab === t.id
                    ? "border-civic text-civic"
                    : "border-transparent text-gray-500 hover:text-gray-800"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div className="min-h-0 flex-1">
            {tab === "chat" && <ChatPanel property={property} />}
            {tab === "avatar" && <AvatarPanel />}
            {tab === "call" && <CallPanel />}
          </div>
        </section>
      </main>
    </div>
  );
}
