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

## 8. System Architecture (high level)

```
        USER QUESTION (text · voice · avatar)
                      │
                      ▼
        ┌─────────────────────────────┐
        │ 1. QUERY CLASSIFIER          │  intent · bureau ·
        │    (fast LLM)                │  relevant titles ·
        └──────────────┬───────────────┘  urgency · confidence
                       │
         ┌─────────────┴──────────────┐
         ▼                            ▼
  ┌──────────────┐            ┌───────────────┐
  │ 2. ADDRESS   │            │ 3. RISK GATE  │
  │   RESOLVE    │            │  LOW/MED/HIGH │
  │  → zoning    │            └───────────────┘
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────────────┐
  │ 4. MULTI-CORPUS RETRIEVAL         │  parallel per-title
  │    (vector knowledge base)        │  queries · dedupe ·
  └──────────────┬────────────────────┘  top results
                 │
                 ▼
  ┌──────────────────────────────────┐
  │ 5. ANSWER AGENT (LLM + tools)     │  grounded answer ·
  │    retrieve / resolve / risk      │  streamed
  └──────────────┬────────────────────┘
                 │
                 ▼
  ┌──────────────────────────────────┐
  │ 6. RESPONSE                       │  answer + citations +
  │                                    │  risk badge + next steps
  └──────────────────────────────────┘
```

### 8.1 Core components
- **Query classifier** — a fast LLM call that returns structured JSON: `intent`, `bureau`, `relevant_titles`, `requires_property`, `urgency`, `confidence`.
- **Knowledge base** — a vector-indexed corpus of city code titles, code guides, administrative rules, and program guides, with hierarchical chunking.
- **Retrieval layer** — runs focused per-title queries, merges and de-duplicates results, boosts on-corpus matches, returns the top passages.
- **Answer agent** — an LLM agent with tools for retrieval, address resolution, and risk assessment; streams its response.
- **Address resolution** — geocode an address to a point, then look up the parcel's zoning attributes from the city GIS service.
- **Risk engine** — pattern + classifier-driven risk scoring.
- **Channel adapters** — web (streaming + map UI), phone (telephony webhook + TTS), avatar (real-time avatar SDK).
- **Conversation memory** — per-session context so follow-ups work.

### 8.2 Data corpus
The knowledge base ingests Portland City Code titles covering, at minimum: zoning, building regulations, plumbing, electrical, heating/ventilation, fire, trees, signs, noise control, property maintenance, erosion/sediment control, public improvements, floating structures, and original-art murals — plus code guides, sewer/stormwater guidance, and transportation rules. Large documents are split to fit ingestion limits; updates flow through an automated sync.

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
