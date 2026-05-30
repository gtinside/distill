# Distill

iOS app that synthesizes daily AI digests from user-defined Topics. Users define free-text Topics (e.g. "Fed policy", "ultra-low latency systems") and receive a Digest of Topic Cards — each a TL;DR + bullets + sources — pushed daily or refreshable on demand.

## Domain Language

See `CONTEXT.md` for the canonical glossary (Digest, Topic Card, Topic, User, Source, Delivery Time). Use these terms in code, comments, and issues — not synonyms.

## Architecture

- **iOS client**: SwiftUI, iPhone-first
- **Backend**: Python, deployed as a long-running Railway worker
- **Database + Auth**: Supabase (PostgreSQL). Sign in with Apple via Supabase Auth.
- **Push notifications**: Firebase Cloud Messaging → APNs
- **Source fetching**: Exa.ai semantic search API
- **Synthesis**: Claude Sonnet (one call per Topic Card, structured JSON output)

See `docs/adr/` for key architectural decisions. See `docs/PRD.md` for full requirements and module breakdown.

## Backend Modules

- `SynthesisEngine` — pure function: Topic + Exa.ai results → TopicCard. Tested with fixtures, no live API calls in CI.
- `DigestOrchestrator` — fans out SynthesisEngine across all User Topics, handles partial failure + 3 retries per card.
- `SchedulerWorker` — polls Supabase every 60s for Users with a matching Delivery Time, triggers DigestOrchestrator.
- `PushNotificationService` — sends personalised FCM push after Digest generation.
- `APILayer` — REST endpoints consumed by the iOS client.

## Key Non-Obvious Decisions

- **Railway worker, not serverless**: Supabase Edge Functions cap at 2 min; multi-topic synthesis needs more headroom. See `docs/adr/0001`.
- **Partial Digest on failure**: Failed Topic Cards show an error state; the Digest is still delivered. See `docs/adr/0002`.
- **One Digest at a time**: Only the current Digest is stored per User. No history.
- **On-demand refresh rate limit**: Once per hour per Topic Card, enforced server-side via `last_refreshed_at`.

## Environment Variables

See `.env.example` for the full list. Required:
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `ANTHROPIC_API_KEY`
- `EXA_API_KEY`
- `FIREBASE_SERVICE_ACCOUNT` (JSON)

## Implementation Status

Issues tracked at https://github.com/gtinside/distill/issues — 13 vertical slices, starting with #2 (external services setup).
