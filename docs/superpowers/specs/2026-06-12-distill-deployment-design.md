# Distill Deployment Strategy — Design Spec

**Date:** 2026-06-12
**Status:** Approved for implementation (runbook)
**Authors:** gtinside + Claude

## Summary

Deploy Distill to **full production at near-zero recurring cost**. Web on Vercel
Hobby (free), the FastAPI worker on Railway (~$5/mo always-on), Supabase Free for
Postgres + Auth, Resend Free for email. Everything deploys from the existing
GitHub repo on push. The one limitation of the free path — real email delivery —
is sequenced into a cheap Phase 2 (add a domain, ~$12/yr).

## Goals

- Real users: magic-link auth, live trending, per-user daily Digest.
- Minimize recurring cost (free tiers everywhere except the always-on worker).
- Git-driven deploys (push to `main` ships both tiers).
- No code changes to go live — configuration only.

## Non-Goals (now)

- $0 backend via a GitHub Actions cron + serverless API restructure (future).
- Auto-applied migrations in CI; staging environment; observability/alerting.
- Custom domain in Phase 1 (deferred to Phase 2 for real email).

## Constraints / key facts

- The backend is a **long-running process** (60s scheduler poll + the API in one
  process, `main.py`), so it **must be always-on** — rules out hosts whose free
  tier sleeps (e.g. Render free sleeps after 15 min and would kill the scheduler).
- **GitHub Pages cannot host the web app** — it is server-side (SSR, server
  actions, BFF, `@supabase/ssr` cookie auth, proxy). GitHub is the source repo
  that Vercel/Railway deploy from, not the host.
- **No CORS needed**: the browser never calls the backend directly; the Vercel
  BFF proxies server-to-server.
- **Email needs a verified domain**: Resend only sends to arbitrary recipients
  from a verified domain; its shared sender delivers only to the account owner.
  Supabase's built-in auth email works without a domain but is rate-limited and
  low-deliverability. Hence the phased email path below.

## Topology

| Tier | Host | Cost | Root dir | Deploys from |
|---|---|---|---|---|
| Web (Next.js) | Vercel Hobby | Free | `web/` | GitHub push → auto-build |
| Backend (FastAPI + scheduler) | Railway | ~$5/mo always-on | `backend/` | GitHub push → auto-build |
| DB + Auth | Supabase Free | Free | — | Migrations via CLI/SQL editor |
| Email | Resend Free (3k/mo) | Free | — | Domain needed for real recipients |
| AI | Anthropic + Exa | Pay-per-use | — | — |

## CI/CD

- **Vercel**: connect repo, root directory `web/`. Push to `main` → production
  deploy; PRs → preview URLs.
- **Railway**: service from repo, root `backend/`, start via existing `Procfile`.
  Push to `main` → deploy.
- One repo, one `git push` ships both.

## Configuration & secrets

Set in each platform dashboard; never commit. `.env*` stays gitignored.

**Vercel env**
- `NEXT_PUBLIC_DEMO_MODE=false`
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `DISTILL_API_URL` = Railway public URL

**Railway env**
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`
- `ANTHROPIC_API_KEY`, `EXA_API_KEY`
- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- `APP_BASE_URL` = Vercel URL
- `TRENDING_REFRESH_UTC` (default `05:00`)

**Supabase**
- Auth → Providers: enable Email (magic link).
- Auth → URL Configuration: add `https://<app>.vercel.app/auth/callback` to the
  redirect allowlist; set Site URL to the Vercel URL.

## Migrations

Apply in order (via `supabase db push` or the SQL editor):
1. `supabase/migrations/20260602000000_initial_schema.sql`
2. `supabase/migrations/20260610000000_web_email_auth.sql`
3. `supabase/migrations/20260611000000_trending.sql`

Manual on deploy for now; auto-apply via a GitHub Action is a future nicety.

## Phased email path

- **Phase 1 — now (free):** full app live on `*.vercel.app` + Railway. Trending,
  follow, browsing, low-volume magic-link sign-in work. Digests generate and
  store; email delivery limited to the account owner's address until a domain
  exists.
- **Phase 2 — when ready (~$12/yr):** buy a domain, verify it in Resend (SPF/DKIM
  DNS), point `RESEND_FROM_EMAIL` at it, optionally move the app to the domain and
  wire Resend as Supabase's custom SMTP. Digests then reach all users. Config +
  DNS only — no code change.

## Verification (post-deploy)

- Web: `https://<app>.vercel.app/` renders the trending front page (logged-out).
- Auth: magic link sign-in completes and lands on the signed-in blend.
- Backend: `GET <railway-url>/health` → `{"status":"ok"}`; `GET /trending`
  returns cards after the first scheduler run (or a manual trigger).
- Follow a trending topic → it appears in Your Digest.
- (Phase 2) A test user receives the daily digest email.

## Cost summary

- Recurring: **~$5/mo** (Railway) + pay-per-use AI (shared daily trending ≈ 10
  Claude/Exa calls; per-user digests scale with users × topics).
- Later: **+~$12/yr** domain to unlock real email.

## Risks

- **Email gated on domain** — the core daily-digest value loop needs Phase 2 for
  real recipients. Mitigation: ship Phase 1, add domain promptly.
- **AI spend scales with users×topics** — mitigations: shared trending (already),
  the 10-topic cap, once-daily generation; revisit caching if usage grows.
- **Supabase free pause** — projects pause after 7 days inactivity; the 60s
  scheduler keeps it active, so only a relevance if the backend is down long-term.
- **Single backend instance** — no redundancy; acceptable at this scale.
