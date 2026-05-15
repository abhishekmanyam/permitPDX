import type { AgentEvent, Property } from "./types";

// In production the backend serves this app, so same-origin "" works.
// For local dev set VITE_API_BASE to the backend URL.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function* streamChat(
  message: string,
  sessionId: string,
  propertyContext?: Property | null,
): AsyncGenerator<AgentEvent> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      property_context: propertyContext ?? undefined,
    }),
  });
  if (!res.body) throw new Error("No response stream");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      try {
        yield JSON.parse(line.slice(5).trim()) as AgentEvent;
      } catch {
        /* ignore malformed chunk */
      }
    }
  }
}

export async function resolveAddress(address: string): Promise<Property> {
  const res = await fetch(`${API_BASE}/api/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address }),
  });
  return res.json();
}

export async function reverseGeocode(lat: number, lon: number): Promise<Property> {
  const res = await fetch(`${API_BASE}/api/reverse-geocode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lon }),
  });
  return res.json();
}

export async function avatarSession(): Promise<Record<string, string>> {
  const res = await fetch(`${API_BASE}/api/avatar/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sandbox: true }),
  });
  return res.json();
}
