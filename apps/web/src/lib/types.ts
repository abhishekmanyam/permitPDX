export interface Source {
  n: number;
  title: string;
  uri: string;
  score: number;
  snippet: string;
}

export interface Classification {
  intent: string;
  bureau: string;
  relevant_titles: string[];
  requires_property: boolean;
  urgency: string;
  confidence: number;
}

export interface Risk {
  level: "LOW" | "MEDIUM" | "HIGH";
  category: string;
  reason: string;
}

export interface Property {
  address: string;
  lat: number;
  lon: number;
  zone?: string;
  zone_desc?: string;
  overlays?: string;
  comp_plan?: string;
  error?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
  risk?: Risk;
  classification?: Classification;
  status?: string;
  streaming?: boolean;
}

export type AgentEvent =
  | { type: "meta"; classification: Classification; risk: Risk; sources: Source[] }
  | { type: "status"; stage: string; text: string }
  | { type: "token"; text: string }
  | { type: "phrase"; text: string }
  | { type: "blocked"; by: string }
  | { type: "error"; message: string }
  | { type: "done" };
