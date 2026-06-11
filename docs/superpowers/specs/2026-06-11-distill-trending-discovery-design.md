# Distill Trending & Discovery — Design Spec

**Date:** 2026-06-11
**Status:** Approved for implementation
**Authors:** gtinside + Claude

## Summary

Turn Distill from a private, define-everything tool into a **destination with a
public trending front page** plus personal discovery. A logged-out visitor lands
on full **Trending Topic Cards** (instant value, SEO, shareable). A signed-in
user sees **their Digest** plus **trending topics they aren't following yet**,
each one-tap **Followable**. This fixes the cold-start problem and adds a
discovery/retention loop the current product lacks.

Trending is **curated now, architected to become world-derived later** (the
selection source is isolated behind one interface). Domain language (Digest,
Topic Card, Topic, Source, Delivery Time) is unchanged; "Trending" is a new,
shared/global concept layered on top.

## Goals

- Public, indexable trending front page with full Topic Cards (no auth).
- Signed-in blend: your Topics first, then "Trending — not following" with Follow.
- Reuse the existing synthesis pipeline and Topic/Topic Card model.
- Keep the app fully runnable in demo mode (no backend needed).

## Non-Goals (v1)

- World-derived or aggregate-of-users trend detection (architected for, not built).
- Trending in the daily email (email stays your-topics-only).
- Per-user trending ranking/personalization beyond "not already followed".

## Concept — three states of `/`

1. **Logged-out — trending front page.** Server-rendered, public, full Trending
   Topic Cards. Header CTA: "Sign in to follow topics & get your daily digest."
2. **Signed-in — the blend.** `Your Digest` (followed Topics) on top; `Trending —
   not following` below, each card with a **Follow** button. Following adds the
   Topic to the user's list (respects the 10-cap) and it moves into Your Digest.
3. **Topics tab** unchanged for management; "Follow from trending" is the easy
   path in, typing your own is the power-user path. New-user onboarding may start
   from "pick from trending" instead of a blank box.

## Trending mechanics

- **Shared global digest.** The backend maintains one global set of Trending
  Topic Cards, generated **once daily** and served to everyone (compute once,
  serve to all).
- **Curated selection (hybrid).** Trending Topics come from an admin-maintained
  list; only the *selection* is curated — card *content* is always freshly
  synthesized. Isolated behind `get_trending_topics()` so it can later be swapped
  for world-derived detection without UI/pipeline changes.

## Backend changes

### Data model (2 new tables)

- **`trending_topics`**: `id`, `phrase`, `rank`, `active` (bool, default true),
  `created_at`. Seeded via migration.
- **`trending_cards`**: `id`, `trending_topic_id` (fk), `tldr`, `bullets`
  (jsonb), `sources` (jsonb), `status` ('ok'|'error'), `generated_at`. One
  current row per trending topic (upsert on generation). Public-readable.

### Modules

- **`SynthesisEngine`** — unchanged (pure: phrase + sources → Topic Card).
- **`DigestOrchestrator`** — refactor to expose a core `generate_cards(topics)`
  over any `list[(id, phrase)]`; `generate(user_id)` becomes a thin wrapper.
  Trending reuses this exact path, including 3-retry + partial-failure (ADR-0002).
- **`SchedulerWorker`** — add a **daily global-trending pass**: once per day at a
  configured UTC time (guarded by a "last generated" check), generate
  `trending_cards` for all active trending topics and upsert them. Per-user
  digests unchanged.
- **`SupabaseDb`** — add `get_trending_topics()`, `get_trending_cards()` (global
  digest joined to topics, ordered by rank), `save_trending_cards(cards)`.

### API

- **`GET /trending`** — **public** (bypasses auth). Returns the global trending
  digest: a list of cards shaped like existing Topic Cards plus the trending
  `phrase` and `trending_topic_id`. Requires adding `/trending` to
  `AuthMiddleware`'s public allowlist (today only `/health` is public).
- **Follow** reuses **`POST /topics {phrase}`** (existing 3–60 validation +
  10-cap). No new endpoint. "Not following" is computed by diffing trending
  against the user's topic phrases (case-insensitive) in the web BFF.

## Web changes

- **`api.ts`**: `getTrending()` (demo: seeded trending fixtures; real:
  `GET /trending`). Follow → existing `createTopic(phrase)`.
- **Home route `/`**: logged-out → trending front page; signed-in → blend (Your
  Digest + Trending-not-following). Replaces the current redirect-only `/`.
- **`FollowButton`** on trending cards (signed-in only) → `createTopic` + revalidate.
- **Onboarding**: offer "pick from trending to start" alongside free-text entry.
- **Demo mode**: trending fixtures so the whole experience runs offline.

### Card-shape contract (web ↔ backend)

`GET /trending` returns:
```json
{ "generated_at": "ISO", "cards": [
  { "trending_topic_id": "tt1", "phrase": "EU AI regulation",
    "status": "ok", "tldr": "…", "bullets": ["…"],
    "sources": [{"title":"…","url":"…"}] } ] }
```
Error cards omit tldr/bullets/sources and carry `"status": "error"`.

## Visual direction

Complete the **Refined dark / focus** theme (warm near-black canvas, single amber
accent, Fraunces display serif + Hanken Grotesk body + JetBrains Mono labels,
restrained staggered card reveal). Applied across all screens, including the new
front page.

## Testing

- **Backend**: keep all existing tests green. Add: `generate_cards` over a topic
  list (incl. partial failure), trending generation/persistence, public
  `GET /trending` returns without auth, `GET /trending` shape.
- **Web**: `npm run build` + `npm run lint` clean; app runs in demo mode showing
  trending logged-out and the blend when "signed in" (demo continue).

## Docs

- ADR-0004: trending front page + shared global digest.
- Update `CONTEXT.md` with the **Trending** term.
- Refresh README screenshots (front page, blend).

## Decisions made on the user's behalf

- Email stays your-topics-only for v1.
- Complete the dark theme as part of this work.
- Curated trending seeded via migration (~8–12 timely topics); regenerated daily.
- Trending regeneration cadence: once daily at a fixed UTC time.
