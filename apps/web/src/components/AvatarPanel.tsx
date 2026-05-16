import { useCallback, useEffect, useRef, useState } from "react";
import { LiveAvatarSession } from "@heygen/liveavatar-web-sdk";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

type State = "idle" | "connecting" | "listening" | "speaking" | "error";

export default function AvatarPanel() {
  const [state, setState] = useState<State>("idle");
  const [error, setError] = useState<string | null>(null);
  const [userText, setUserText] = useState("");
  const [avatarText, setAvatarText] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const sessionRef = useRef<LiveAvatarSession | null>(null);
  const tokenRef = useRef<string | null>(null);

  const start = useCallback(async () => {
    setState("connecting");
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/avatar/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sandbox: true }),
      });
      const data = await resp.json();
      if (!data.session_token) throw new Error(data.error || "No session token");
      tokenRef.current = data.session_token;

      // The SDK handles /sessions/start, LiveKit transport, mic + VAD, and TTS.
      const session = new LiveAvatarSession(data.session_token) as any;
      sessionRef.current = session;

      session.on("session.stream_ready", () => {
        if (videoRef.current) session.attach(videoRef.current);
        session.voiceChat.start();
        setState("listening");
      });
      session.on("user.transcription", (e: any) => setUserText(e?.text || ""));
      session.on("avatar.transcription", (e: any) => setAvatarText(e?.text || ""));
      session.on("avatar.speak_started", () => setState("speaking"));
      session.on("avatar.speak_ended", () => setState("listening"));
      session.on("session.stopped", () => setState("idle"));

      await session.start();
    } catch (e: any) {
      setError(e?.message || "Failed to connect");
      setState("error");
    }
  }, []);

  const stop = useCallback(() => {
    try {
      sessionRef.current?.stop();
    } catch {
      /* ignore */
    }
    if (tokenRef.current) {
      fetch(`${API_BASE}/api/avatar/stop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_token: tokenRef.current }),
      }).catch(() => {});
    }
    sessionRef.current = null;
    tokenRef.current = null;
    setState("idle");
    setUserText("");
    setAvatarText("");
  }, []);

  useEffect(() => () => stop(), [stop]);

  const active = state !== "idle" && state !== "error";

  return (
    <div className="relative flex h-full flex-col bg-ink">
      <div className="flex flex-1 items-center justify-center overflow-hidden">
        {active ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="px-8 text-center">
            <div className="mx-auto mb-5 h-px w-12 bg-cream/20" />
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cream/40">
              Live Avatar
            </div>
            <p className="mx-auto mt-3 max-w-xs font-display text-xl font-medium text-cream">
              Talk face-to-face with the Portland Permit Assistant
            </p>
            <p className="mt-2 text-xs text-cream/40">
              Voice in, voice out — answers cited to city code.
            </p>
          </div>
        )}
      </div>

      {active && (
        <div className="absolute left-3 top-3 flex items-center gap-2 rounded-lg bg-black/60 px-3 py-1.5 text-xs text-white">
          <span
            className={`h-2 w-2 rounded-full ${
              state === "speaking"
                ? "bg-civic"
                : state === "listening"
                  ? "bg-gold"
                  : "bg-cream/60"
            } animate-pulse`}
          />
          {state === "connecting" && "Connecting…"}
          {state === "listening" && "Listening…"}
          {state === "speaking" && "Speaking"}
        </div>
      )}

      {active && (avatarText || userText) && (
        <div className="absolute bottom-20 left-3 right-3 space-y-2">
          {avatarText && (
            <div className="max-h-24 overflow-y-auto rounded-lg bg-black/70 px-3 py-2 text-sm text-white">
              {avatarText}
            </div>
          )}
          {userText && (
            <div className="rounded-lg bg-white/10 px-3 py-2 text-sm italic text-gray-300">
              You: {userText}
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="absolute bottom-20 left-3 right-3 rounded-lg bg-red-500/90 px-3 py-2 text-sm text-white">
          {error}
        </div>
      )}

      <div className="flex justify-center p-3">
        <button
          onClick={active ? stop : start}
          disabled={state === "connecting"}
          className={`rounded-full px-7 py-2.5 text-sm font-semibold text-cream transition disabled:opacity-50 ${
            active ? "bg-red-700 hover:bg-red-800" : "bg-civic hover:bg-civic-dark"
          }`}
        >
          {active ? "End session" : "Start avatar"}
        </button>
      </div>
    </div>
  );
}
