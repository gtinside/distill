# Distill Web — Design Spec

**Date:** 2026-06-10
**Status:** Approved for planning
**Authors:** gtinside + Claude

## Summary

Convert Distill from a native iOS app to a web application, motivated by the
decision not to pay for an Apple Developer account. The valuable, well-tested
Python backend (synthesis pipeline, orchestration, scheduling, API) is preserved
unchanged. We add a Next.js web client and replace the two Apple-gated features —
push notifications and Sign in with Apple — with email delivery and Supabase
magic-link auth respectively.

Domain language is unchanged: **Digest**, **Topic Card**, **Topic**, **User**,
**Source**, **Delivery Time** (see `CONTEXT.md`).

## Goals

- Full feature parity with the iOS PRD, adapted to the web.
- Reuse the existing FastAPI backend + Supabase with minimal change.
- Deliver the daily Digest by email (the primary surface for most users).
- Zero ongoing platform fees (no Apple Developer account).

## Non-Goals

- Offline reading (the iOS `OfflineCacheModule`). Dropped: low value for a
  text app read primarily online; the delivered email is the offline fallback.
- PWA / web push notifications. Email is the only proactive channel.
- Native mobile apps. The `ios/` tree is retained but marked deprecated.
- Migrating history/multi-Digest storage. Still one current Digest per User.

## Architecture

Three deployables:

1. **Next.js web client** (Vercel) — UI plus a thin BFF layer. The Supabase
   session lives in httpOnly cookies via `@supabase/ssr`. Server components and
   route handlers attach the user's access token to FastAPI calls; no business
   logic is duplicated client-side.
2. **FastAPI backend** (Railway) — unchanged REST surface. The existing
   `AuthMiddleware` already validates Supabase JWTs, so authentication needs
   **no backend changes**. The only swap is push → email.
3. **Supabase** — PostgreSQL + Auth. Auth provider becomes magic link. Schema
   gains one field (`timezone`); the device-token field becomes vestigial.

External services: **Exa.ai** (sources) and **Claude Sonnet** (synthesis) are
unchanged. A transactional email provider is added for the Digest email.
Magic-link emails are sent by Supabase Auth itself.

### Client ↔ backend pattern (BFF, "Approach B")

The browser never calls FastAPI directly and never holds the access token in
JavaScript. Flow:

1. Request → Next.js middleware checks the Supabase cookie session → redirect to
   `/signin` if absent.
2. Magic-link click → callback route sets httpOnly session cookies.
3. Server component fetches `GET /digest` / `GET /topics` from FastAPI with the
   bearer token read from the cookie → server-rendered.
4. Mutations run via server actions / route handlers → FastAPI → `revalidate`.

This keeps FastAPI as the single source of truth for all validation and
rate-limiting (3–60 char Topic names, 10-Topic cap, once-per-hour refresh).

## Backend Changes (minimal)

| Module | Change |
|---|---|
| `SynthesisEngine` | None |
| `DigestOrchestrator` | None |
| `SchedulerWorker` | Call `EmailDigestService` instead of `PushNotificationService` after digest generation; compare Delivery Time against the User's stored `timezone` |
| `APILayer` | None to existing endpoints; device-token registration becomes vestigial |
| `SupabaseDb` | Read/write the new `timezone` field on settings |
| `PushNotificationService` | **Replaced** by `EmailDigestService` |

**`EmailDigestService`** — formats the Digest as HTML email and sends it via
**Resend** (recommended; swappable for Postmark/SendGrid/SMTP). Same input as the
old push service (the User's Digest + Topic names), same call site. The email
includes the Topic Cards and a prominent "Open in Distill" deep link.

**Environment variables:** add `RESEND_API_KEY`; remove `FIREBASE_SERVICE_ACCOUNT`.

## Frontend Modules (Next.js App Router)

Mirrors the PRD module breakdown:

- **Auth** — magic-link sign-in page, callback route, session-refresh middleware,
  redirect-to-`/signin` for unauthenticated requests. Built on `@supabase/ssr`.
- **Onboarding wizard** —
  - *Topics screen*: free-text entry, tappable example chips, 3–60 char
    validation, ≤10 Topics enforced (Add disables at 10).
  - *Delivery Time screen*: time picker defaulting to 7:00 AM; browser timezone
    captured via `Intl.DateTimeFormat` and stored.
  - On finish: `POST /digest/generate` so the first Digest exists immediately.
- **Digest feed** — server-rendered list of Topic Cards (TL;DR, bullets,
  sources). Per-card refresh button → `POST /digest/topics/:id/refresh`, with
  `429` surfaced as "Refresh available at HH:MM". Failed cards show an error
  state with a Retry action (partial-Digest principle, ADR-0002).
- **Topics tab** — add / delete / drag-to-reorder (`PATCH /topics/:id`
  `display_order`); entry point to Settings.
- **Settings** — change Delivery Time (reusing stored timezone); Sign out
  (clears session cookies → `/signin`).
- **API client** — one typed module; all calls flow server-side through the BFF
  with the bearer token attached.

## Data Model Change

Add `timezone` (IANA string, e.g. `America/New_York`) to User settings alongside
`delivery_time`. iOS relied on device-local time; the web has no equivalent, so
the timezone is captured at onboarding and used by `SchedulerWorker` to match the
Delivery Time. Default to the browser timezone; editable in Settings.

## User Experience

A new User, Maya:

1. **Sign in** — visits the site, no session → `/signin`, enters email, receives
   a magic link, clicks it, is signed in (no password).
2. **Onboarding (Topics)** — taps example chips and types her own; validation
   enforces 3–60 chars and the 10-Topic cap.
3. **Onboarding (Delivery Time)** — picks a time (default 7:00 AM); browser
   timezone captured silently.
4. **First Digest** — on finish, `POST /digest/generate` runs; the feed populates
   with Topic Cards within ~a minute. Immediate value, no waiting for tomorrow.
5. **Daily email** — at her Delivery Time, `SchedulerWorker` (matching her
   timezone) regenerates the Digest and `EmailDigestService` emails the rendered
   Topic Cards with an "Open in Distill" link. For most days the email is the
   product.
6. **Return visits** — valid cookie session → straight to today's Digest. Only
   the current Digest exists; no backlog.
7. **On-demand refresh** — refresh a stale card; a too-soon retry shows
   "Refresh available at HH:MM" (429).
8. **Failed card** — an isolated synthesis failure shows an error card with
   Retry; the rest of the Digest is unaffected.
9. **Manage Topics** — add / delete / drag-reorder; reorder updates both feed and
   email order.
10. **Settings** — change Delivery Time, Sign out.

### Known UX seams (accepted for v1)

- **Magic-link friction**: one extra click vs a password; mitigated by
  long-lived sessions. Include a "link expired — resend" state.
- **Email render quality matters as much as the web UI** — the HTML email is the
  primary surface for most users and is a first-class design artifact.
- **Travel / timezone change**: Delivery Time follows the timezone stored at
  onboarding until the User updates Settings. Acceptable for v1.
- **No offline**: the already-delivered email is the offline fallback.

## Testing

- **Backend**: keep the existing suite green. Replace
  `test_push_notification_service.py` with `test_email_digest_service.py` (format
  + send against a mock). No live external APIs in CI — unchanged discipline.
- **Frontend**: component tests (Vitest + React Testing Library) for the
  validation-heavy forms (Topic entry, onboarding); 1–2 Playwright e2e covering
  sign-in → onboarding → first Digest with FastAPI mocked.

## Repo & Docs

- Add `web/` alongside `backend/` and `ios/`.
- Mark `ios/` deprecated in its README (retained, not deleted).
- **ADR-0003: web client + email delivery** — record the pivot off Apple
  (push → email, Sign in with Apple → magic link, Next.js BFF).
- Update `CONTEXT.md` so "push notification" language becomes "email delivery".

## Decisions Made

- **Email provider**: **Resend** (confirmed 2026-06-10).

## Risks

- **Email deliverability** — digests landing in spam would silently kill the daily
  loop. Requires proper SPF/DKIM/domain setup with the chosen provider.
- **Timezone correctness** — the one genuinely new piece of logic; needs explicit
  tests around the `SchedulerWorker` match window.
- **Magic-link UX** — some users dislike inbox round-trips; monitor and consider
  adding an OTP-code or OAuth option later if drop-off is high.
