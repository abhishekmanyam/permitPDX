# Product Requirements Document — Portland Permit Assistant

**Status:** Draft v1.0
**Date:** May 15, 2026
**Owner:** Product (Hackathon Team)
**Sponsor:** Bureau of Planning & Sustainability (BPS), City of Portland

---

## 1. Overview

The Portland Permit Assistant is a multi-channel AI assistant that helps residents, property owners, contractors, and small-business owners understand which City of Portland rules, codes, and permits apply to a real-world property situation — and gives them clear, cited answers from authoritative city sources.

City code is large, fragmented across dozens of titles and multiple bureaus, and written for specialists. Most people don't know which title governs a fence height, a backyard ADU, a deck, a sign, or a tree removal — let alone how their specific lot's zoning and overlays change the answer. The result is wasted trips to the permit counter, stalled projects, unpermitted work, and expensive rework.

This product collapses that gap: ask a plain-language question, optionally anchor it to an address, and get an accurate answer grounded in the actual city code with citations.

---

## 2. Problem Statement

- **Code is inaccessible.** Portland City Code spans ~14+ titles (zoning, building, plumbing, electrical, fire, trees, signs, noise, property maintenance, and more), plus code guides, administrative rules, and bureau program guides. Finding the relevant passage requires knowing the structure in advance.
- **Answers are property-specific.** The same question ("Can I build this?") has different answers depending on a parcel's zone, overlays, and comprehensive plan designation. Generic answers are often wrong.
- **Bureaus are siloed.** A single project can touch BPS, BDS, PBOT, and BES. Residents don't know who owns what.
- **Access is uneven.** Not everyone can navigate a web app — some need to call, some need an in-person/kiosk experience, some are on a job site.
- **Risk is invisible.** Some questions touch structural safety or environmental health where a wrong DIY answer is dangerous. Users aren't warned when they should consult a licensed professional.

---

## 3. Goals & Non-Goals

### 3.1 Goals
1. Let any resident get an accurate, plain-language answer about Portland city code in under a minute.
2. Ground every answer in authoritative city sources with visible, clickable citations.
3. Make answers property-aware: resolve an address to its zoning context and use it.
4. Meet users where they are — web chat, phone call, and an interactive avatar/kiosk experience.
5. Flag high-risk topics and steer users to professional help when appropriate.

### 3.2 Non-Goals
- Not a replacement for an official permit determination or a plan reviewer.
- Not a permit *submission* portal — it informs and routes, it does not file applications.
- Not legal advice. Answers are informational with clear disclaimers.
- No account system or saved user history in v1.

---

## 4. Target Users & Personas

| Persona | Need | Primary channel |
|---|---|---|
| **Homeowner** ("Can I build a fence/ADU/deck?") | Plain answers before starting a project | Web chat |
| **Contractor** | Quick code lookups, permit requirements per parcel | Web chat / phone |
| **Small-business owner** | Signage, occupancy, change-of-use rules | Web chat |
| **Elderly / low-digital-literacy resident** | Talk to someone, no typing | Phone call |
| **On-site worker** | Hands-free answer in the field | Phone call |
| **Walk-in / kiosk visitor** | Face-to-face guided experience | Avatar kiosk |
| **City staff (BPS)** | Reduce repetitive counter questions | (Indirect benefit) |

---

## 5. User Stories

- As a homeowner, I can ask "How tall can my backyard fence be?" and get a cited answer.
- As a homeowner, I can enter my address and get answers tailored to my lot's zoning and overlays.
- As a contractor, I can ask a follow-up question and the assistant keeps the conversation context.
- As a caller, I can phone a number and have a natural spoken conversation with the assistant.
- As a kiosk visitor, I can speak to an on-screen avatar and watch it answer me.
- As any user, I can see exactly which code section an answer came from and open the source.
- As any user, when my question touches structural or environmental safety, I'm told to consult a licensed professional.

---

## 6. Functional Requirements

### 6.1 Conversational Q&A (all channels)
- Accept a free-text or spoken question.
- Classify the question to understand intent, the responsible bureau(s), and which code titles are relevant.
- Retrieve the most relevant passages from the city code corpus.
- Generate a grounded answer that cites its sources.
- Support multi-turn follow-up questions within a session.

### 6.2 Property awareness
- Accept an address (typed, searched on a map, or spoken).
- Resolve the address to a geographic point and look up its property context: zone, zone description, overlays, comprehensive plan designation, historic designation.
- Use that property context to scope and tailor the answer.
- Support reverse geocoding (map click → address + property context).

### 6.3 Retrieval & citations
- Index the full Portland City Code corpus plus code guides, administrative rules, and bureau program guides.
- Query the corpus per relevant title and merge results, de-duplicating by source.
- Every factual claim in an answer maps to a numbered citation `[N]`.
- Citations are clickable and lead to the source passage/document.

### 6.4 Risk gating
- Detect when a question touches structural safety, environmental/health hazards, or land division.
- Assign a risk level: LOW / MEDIUM / HIGH.
- Surface a visible risk callout on MEDIUM+ answers ("Heads up — consult a licensed professional").

### 6.5 Channels
- **Web chat:** streaming responses, an interactive map for address selection, suggested starter questions, citation badges, a property summary card, and risk callouts.
- **Phone:** a published phone number; natural spoken Q&A with speech recognition and text-to-speech; graceful handling of long lookups so the call doesn't drop.
- **Avatar / kiosk:** an in-browser talking avatar that listens and responds with synced speech, for walk-in/kiosk settings.

### 6.6 Answer format
- **Text channels:** markdown with headings, numbered citations, and a "next steps" section.
- **Voice channels:** natural spoken language, concise (≤ ~4 sentences), no markdown or inline citation markers.

---

## 7. Non-Functional Requirements

| Area | Requirement |
|---|---|
| **Accuracy** | Answers must be grounded in retrieved sources; no unsupported claims. Disclaimer shown that answers are informational. |
| **Latency** | Question classification fast (sub-second). First token of a text answer ideally < 3s. Voice channel must not drop on slow lookups. |
| **Availability** | Public-facing; should tolerate normal civic traffic with no idle-heavy infrastructure. |
| **Accessibility** | Multi-channel by design (web, voice, avatar). Web UI meets WCAG AA; voice channel serves low-digital-literacy users. |
| **Trust & tone** | Civic, clear, neutral — not marketing-y. Always cite. Always disclaim. |
| **Cost** | Usage-based / serverless where possible; minimal idle cost. |
| **Privacy** | No accounts, no PII storage in v1. Addresses used transiently for property lookup. |
| **Data freshness** | Corpus updates should propagate without a full redeploy. |

---

## 8. System Architecture

The system is three tiers: a **React web client**, a thin **FastAPI channel backend**, and an **Amazon Bedrock AgentCore Runtime** that holds all agent reasoning. The backend does no reasoning — it adapts each channel (web chat, Twilio voice, HeyGen/LiveAvatar) onto the same runtime and relays the streamed events back.

### 8.1 Request flow

```
   WEB (React)        PHONE (Twilio)        AVATAR (LiveAvatar kiosk)
        │                   │                        │
   SSE /api/chat    TwiML /api/voice/*    OpenAI /v1/chat/completions
        └───────────────────┼────────────────────────┘
                             ▼
              ┌──────────────────────────────┐
              │  FastAPI BACKEND (ECS Fargate)│  channel adapters · serves
              │  apps/backend/main.py         │  built React frontend · SSE relay
              └──────────────┬────────────────┘
                             │  invoke_agent_runtime (streamed events)
                             ▼
        ┌────────────────────────────────────────────┐
        │  AGENTCORE RUNTIME — agent/agent.py          │
        │                                              │
        │  contextualize ─ rewrite follow-ups          │  Haiku 4.5
        │       │          using session history       │
        │       ▼                                      │
        │  1. CLASSIFY ─ intent · bureau · titles ·    │  Haiku 4.5
        │       │        requires_property · urgency   │  → structured JSON
        │       ▼                                      │
        │  2. RETRIEVE ─ parallel per-title KB queries │  Bedrock KB
        │       │        merge · dedupe · boost · topN │  (S3 Vectors)
        │       ▼                                      │
        │  3. RISK GATE ─ regex + classifier urgency   │  LOW/MED/HIGH
        │       │         → emits `meta` event         │
        │       ▼                                      │
        │  4. ANSWER AGENT ─ Strands Agent, streamed   │  Sonnet 4.5
        │       resolve_property tool · Guardrail      │  + Bedrock Guardrail
        └────────────────────┬─────────────────────────┘
                             │  token / phrase / meta / done events
                             ▼
            answer + citations + risk badge + next steps
```

The runtime emits a `status` event before each blocking step, one `meta` event (classification, ranked sources, risk), then `token` events for text channels or `phrase` events (sentence-chunked for TTS) for voice/avatar, and a final `done`.

### 8.2 Core components

| Component | Implementation |
|---|---|
| **Web client** | React 19 + Vite + Tailwind 4; Mapbox GL map; `react-markdown` live render; LiveAvatar Web SDK. Consumes SSE from `/api/chat`. |
| **Channel backend** | FastAPI on **ECS Fargate** (512 CPU / 1024 MB), behind an ALB and CloudFront. Serves the built React app same-origin and exposes `/api/chat` (SSE), `/api/resolve`, `/api/reverse-geocode`, `/api/voice/*` (TwiML), `/api/avatar/*`, and an OpenAI-shaped `/v1/chat/completions`. |
| **Agent runtime** | Amazon Bedrock **AgentCore Runtime** (`agent/agent.py`), async generator entrypoint that streams events. |
| **Contextualizer** | Haiku 4.5 call that rewrites follow-ups ("what about side fences?") into standalone search queries using the last 6 turns. |
| **Query classifier** | Single Haiku 4.5 `converse` call returning JSON: `intent`, `bureau`, `relevant_titles`, `requires_property`, `urgency`, `confidence`. Fails safe to a broad, unscoped classification. |
| **Knowledge base** | Bedrock Knowledge Base `61POYN2UXQ` over Portland City Code, backed by an **S3 Vectors** index; embeddings via **Titan Text Embeddings v2** (1024-dim). |
| **Retrieval layer** | `retrieve_multi_corpus` — up to 3 focused per-title KB queries run concurrently (`ThreadPoolExecutor`), 6 results each; merged, deduped by chunk content, boosted ×1.15 when the source file matches the queried title, top 8 returned. |
| **Answer agent** | A **Strands** `Agent` on **Claude Sonnet 4.5**, streaming, seeded with session history and the `resolve_property` tool. Text answers cap at 2048 tokens, voice at 600. |
| **Risk engine** | Regex patterns for structural / environmental / land-division topics plus classifier `urgency`, scored LOW/MED/HIGH. |
| **Address resolution** | US Census geocoder (address → lat/lon) then PortlandMaps ArcGIS (lat/lon → zone, overlays, comp plan). Both keyless. Reverse geocoding adds Mapbox. Implemented both in the backend (`property.py`) and as the agent's `resolve_property` tool. |
| **Conversation memory** | Amazon Bedrock **AgentCore Memory** (`memory.py`), short-term only, keyed by `runtimeSessionId`, 30-day expiry; best-effort (a memory outage degrades to a stateless answer). |
| **Safety guardrail** | A Bedrock **Guardrail** (`1hhciwdq9v9c`) on the answer model in async stream mode; an empty stream is treated as a block and returns a scope message. |

### 8.3 Models

| Role | Model |
|---|---|
| Contextualize + classify | Claude Haiku 4.5 (`us.anthropic.claude-haiku-4-5`) |
| Answer generation | Claude Sonnet 4.5 (`us.anthropic.claude-sonnet-4-5`) |
| Embeddings | Amazon Titan Text Embeddings v2 (1024-dim) |

### 8.4 Data corpus

The knowledge base ingests Portland City Code titles: 4 Original Art Murals, 10 Erosion & Sediment Control, 11 Trees, 17 Public Improvements, 18 Noise Control, 24 Building Regulations, 25 Plumbing, 26 Electrical, 27 Heating & Ventilating, 28 Floating Structures, 29 Property Maintenance, 31 Fire, 32 Signs, and 33 Zoning Code — cleaned text staged in an S3 source bucket and indexed into the S3 Vectors store. Large documents are split to fit ingestion limits; corpus updates re-run the data-source sync without redeploying the runtime.

### 8.5 Deployment & infrastructure

- **Region:** `us-west-2`. All AWS resources provisioned in `infra/` (Terraform for Fargate; Python scripts for the KB and Guardrail). Provisioned ARNs/IDs recorded in `infra/outputs.json`.
- **Backend:** a multi-stage Docker image (Node build of the React app → Python 3.12 + FastAPI/uvicorn serving API and static frontend) pushed to ECR, run as an ECS Fargate service in the default VPC behind an Application Load Balancer.
- **Edge:** CloudFront in front of the ALB for the public HTTPS entry point.
- **Agent runtime:** deployed separately via the `agentcore` toolkit (`agentcore configure`/`launch`); the backend reaches it through `invoke_agent_runtime` by ARN.
- **Config:** all service IDs are environment-overridable with the `infra/outputs.json` values as defaults.

---

## 9. Channel Details

### 9.1 Web chat
- Split layout: interactive map on one side, conversation on the other.
- Address search bar + click-to-pin on the map; the map flies to a resolved property.
- Streaming token-by-token responses.
- Citation badges that expand into a sources panel.
- A property card showing zone / overlay / plan designation.
- Suggested starter questions for first-time users.
- A landing page that explains the three channels and who they serve.

### 9.2 Phone
- A published phone number routed through a telephony webhook.
- Speech-to-text for the caller, text-to-speech for the assistant.
- An async hold pattern: when a lookup takes longer than the telephony timeout, play a brief "let me look that up" message and continue, so the call never drops.
- Recognize goodbye phrases and end the call gracefully.

### 9.3 Avatar / kiosk
- An in-browser talking avatar with real-time speech and lip-sync.
- The avatar uses the voice-optimized answer format (concise, no markdown/citations spoken aloud).
- Designed for unattended kiosk or walk-in counter use.

---

## 10. Design & Tone

- **Voice:** civic, trustworthy, modern — informative, not promotional.
- **Visual:** clean civic palette; clear typographic hierarchy separating headlines, body, and technical labels/stats.
- **Always cite, always disclaim.** Every answer makes its sources visible and notes that it is informational, not an official determination.

---

## 11. Success Metrics

| Metric | Target (hackathon / pilot) |
|---|---|
| Answer relevance (judged) | ≥ 85% of answers rated correct & on-topic |
| Citation coverage | 100% of factual claims have a citation |
| Time to first answer (web) | < 5s end-to-end for a typical question |
| Property resolution success | ≥ 90% of valid Portland addresses resolved |
| Call completion | ≥ 90% of calls answered without a dropped-call failure |
| Risk flagging | 100% of structural/environmental questions show a risk callout |

---

## 12. Assumptions & Dependencies

- Portland City Code text and guidance documents are publicly available for ingestion.
- A public geocoding service and the city GIS zoning service are available with no API key.
- An LLM provider/runtime is available for classification and answer generation.
- A telephony provider and a real-time avatar provider are available for the voice and kiosk channels.
- City code does not change materially during the build window.

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM gives an unsupported or wrong answer | Strict grounding in retrieved sources; visible citations; informational disclaimer |
| Retrieval misses the relevant title | Classifier-driven per-title queries + broad fallback query |
| Telephony webhook timeout drops calls | Async hold/poll pattern |
| Property lookup fails for edge-case addresses | Graceful fallback to a non-property-scoped answer |
| Users treat answers as official determinations | Clear, persistent disclaimer on every channel |
| High-risk DIY questions | Risk gate forces a "consult a professional" callout |

---

## 14. Roadmap (Post-v1)

| Item | Rationale |
|---|---|
| Knowledge-base metadata filters (title / chapter / applicable zones) | Filter retrieval, not just boost — biggest precision gain |
| Re-ranking of retrieved passages | Better top-N selection than raw similarity |
| Human-in-the-loop review queue for HIGH-risk answers | Staff oversight on the riskiest responses |
| Show classifier confidence in the UI | Set user expectations on uncertain answers |
| Permit checklist generator | Given zone + project type, produce a permit-by-permit checklist |
| Deep links to specific permit application forms | Reduce the gap between "what permit" and "apply" |
| Permit fee estimation | Estimate fees from project valuation |
| Per-corpus citation styling | Distinguish code vs. guides vs. admin rules |

---

## 15. Open Questions

1. Should v1 include any session persistence (e.g., a shareable link to a conversation)?
2. What is the official disclaimer language the city will approve?
3. Which bureau owns ongoing content accuracy and corpus updates?
4. Is the avatar/kiosk channel in scope for the hackathon demo, or a stretch goal?
5. What is the escalation path when the assistant can't answer — a phone number, a form, a counter?
