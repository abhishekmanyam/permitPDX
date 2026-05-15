import { useRef, useState } from "react";
import { avatarSession } from "../lib/api";

type Status = "idle" | "connecting" | "ready" | "error";

export default function AvatarPanel() {
  const [status, setStatus] = useState<Status>("idle");
  const [detail, setDetail] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);

  async function start() {
    setStatus("connecting");
    setDetail("Requesting a LiveAvatar session…");
    try {
      const session = await avatarSession();
      if (session.error || !session.token) {
        setStatus("error");
        setDetail(session.error || "No session token returned.");
        return;
      }
      // The HeyGen LiveAvatar SDK consumes session.token to open a WebRTC
      // stream into the <video> element. The avatar's Custom LLM is wired
      // to this backend's /v1/chat/completions endpoint.
      setStatus("ready");
      setDetail(`Session ready (avatar ${session.avatar_id?.slice(0, 8)}…).`);
    } catch (e) {
      setStatus("error");
      setDetail(String(e));
    }
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center">
      <div className="text-xs font-semibold uppercase tracking-wide text-civic">
        Talk to the avatar
      </div>
      <div className="relative aspect-video w-full max-w-md overflow-hidden rounded-xl bg-gray-900">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="h-full w-full object-cover"
        />
        {status !== "ready" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-sm text-gray-300">
            <span className="text-3xl">🧑‍💼</span>
            <span>{status === "idle" ? "Avatar kiosk experience" : detail}</span>
          </div>
        )}
      </div>
      <button
        onClick={start}
        disabled={status === "connecting" || status === "ready"}
        className="rounded-lg bg-civic px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
      >
        {status === "ready" ? "Connected" : "Start avatar session"}
      </button>
      {detail && status !== "idle" && (
        <p className="text-xs text-gray-500">{detail}</p>
      )}
    </div>
  );
}
