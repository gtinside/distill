---
name: tech-decisions
description: All major architectural decisions made for Distill
metadata: 
  node_type: memory
  type: project
  originSessionId: a1e10309-0d26-45af-91f4-788c963f41c1
---

Full stack decisions resolved via /grill-with-docs session on 2026-05-29:

- **iOS:** SwiftUI, iPhone-first (iPad Phase 2)
- **Auth:** Sign in with Apple via Supabase Auth
- **Database:** Supabase (PostgreSQL)
- **Backend worker:** Railway (Python, long-running process polling every 60s) — NOT serverless. See ADR-0001.
- **Source fetching:** Exa.ai (Phase 1 only; user-pinnable RSS/subreddits deferred to Phase 2)
- **LLM synthesis:** Claude Sonnet, one call per Topic Card, structured JSON output
- **Push notifications:** Firebase FCM → APNs
- **Monetization:** Free, 10 Topic hard cap per User, refresh rate-limited once/hour/Topic
- **Digest structure:** TL;DR + 4-5 bullets + source links (Topic Card)
- **Failure handling:** Partial Digest on Topic Card failure (3 retries per card). See ADR-0002.
- **History:** Current Digest only — no archive
- **Onboarding:** Linear 3-screen wizard; auto-generates first Digest on completion
- **Navigation:** Two-tab (Digest, Topics); Settings inside Topics tab
- **Offline:** Last Digest cached to disk (JSON), shown with last-updated timestamp
- **Ordering:** User-draggable Topic order, all cards equal weight

**Why:** Documented to avoid re-litigating decisions in future sessions. All decisions are in ADRs or CONTEXT.md.

**How to apply:** If user asks about stack choices, refer to these. Don't suggest alternatives unless user explicitly wants to revisit.
