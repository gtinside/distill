# Distill Deployment Runbook

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended for a runbook) to work task-by-task. Steps use checkbox (`- [ ]`) syntax. Many steps happen in third-party dashboards and require the human's own accounts, billing, and secrets — Claude can prepare repo files and run verification commands, but cannot click dashboards or hold the user's secrets.

**Goal:** Take Distill to full production at near-zero cost — Vercel (web) + Railway (backend) + Supabase + Resend, all deploying from GitHub on push.

**Architecture:** Stateless Next.js web tier on Vercel proxies (server-side BFF) to a single always-on FastAPI worker on Railway; Supabase provides Postgres + magic-link Auth; Resend sends email. See `docs/superpowers/specs/2026-06-12-distill-deployment-design.md`.

**Tech Stack:** Vercel, Railway, Supabase, Resend, Next.js 16, FastAPI, Python 3.12.

**Prerequisites the human must have:** a GitHub account with this repo pushed (branch `distill-web` or merged to `main`), and the ability to create free accounts on Vercel, Railway (needs a card for the $5 Hobby plan), Supabase, Resend, Anthropic, and Exa. Have these API keys ready: `ANTHROPIC_API_KEY`, `EXA_API_KEY`, `RESEND_API_KEY`.

**Legend:** 🧑 = human-only (dashboard/secret) · 🤖 = Claude can do it (repo edit / verification command).

---

### Task 1: Repo prep — pin Python, add a production env reference 🤖

**Files:**
- Create: `backend/.python-version`
- Create: `docs/deploy/PROD_ENV.md`

- [ ] **Step 1: Pin the backend Python version** (Railway/nixpacks reads this)

Create `backend/.python-version`:

```
3.12
```

- [ ] **Step 2: Add a consolidated production env reference**

Create `docs/deploy/PROD_ENV.md`:

```markdown
# Production environment variables

## Vercel (web) — Project Settings → Environment Variables
NEXT_PUBLIC_DEMO_MODE=false
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<supabase anon key>
DISTILL_API_URL=https://<railway-service>.up.railway.app

## Railway (backend) — Service → Variables
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<supabase anon key>
SUPABASE_SERVICE_ROLE_KEY=<supabase service role key>
SUPABASE_JWT_SECRET=<supabase jwt secret>
ANTHROPIC_API_KEY=<anthropic key>
EXA_API_KEY=<exa key>
RESEND_API_KEY=<resend key>
RESEND_FROM_EMAIL=onboarding@resend.dev   # Phase 1; digest@yourdomain in Phase 2
APP_BASE_URL=https://<app>.vercel.app
TRENDING_REFRESH_UTC=05:00

## Supabase — Authentication → URL Configuration
Site URL:            https://<app>.vercel.app
Redirect allowlist:  https://<app>.vercel.app/auth/callback
```

- [ ] **Step 3: Commit**

```bash
git add backend/.python-version docs/deploy/PROD_ENV.md
git commit -m "chore(deploy): pin backend python, add prod env reference"
git push
```

---

### Task 2: Supabase — project, schema, auth 🧑

**Files:** none (dashboard + `supabase/migrations/*`)

- [ ] **Step 1: Create the project**

At <https://supabase.com> → New project (Free plan). Pick a region near your users. Wait for it to provision.

- [ ] **Step 2: Apply the migrations in order**

Dashboard → SQL Editor → paste and run each file's contents, in this order:
1. `supabase/migrations/20260602000000_initial_schema.sql`
2. `supabase/migrations/20260610000000_web_email_auth.sql`
3. `supabase/migrations/20260611000000_trending.sql`

(Or, with the Supabase CLI linked to the project: `supabase db push`.)

- [ ] **Step 3: Enable magic-link auth**

Authentication → Providers → Email → enable. Ensure "Confirm email" / magic link is on. (Leave Site URL/redirects for Task 5.)

- [ ] **Step 4: Collect the keys** (Project Settings → API, and → API → JWT)

Record for later: Project URL, `anon` key, `service_role` key, JWT Secret.

- [ ] **Step 5: Verify**

SQL Editor: `select count(*) from trending_topics;` → expect `10` (seeded).

---

### Task 3: Railway — deploy the backend worker 🧑 (🤖 verifies)

**Files:** none (uses `backend/Procfile`, `backend/requirements.txt`, `backend/.python-version`)

- [ ] **Step 1: Create the service**

At <https://railway.app> → New Project → Deploy from GitHub repo → select this repo. In the service settings set **Root Directory = `backend`**. Railway (nixpacks) detects Python via `requirements.txt` and runs the `Procfile` `web:` process.

- [ ] **Step 2: Set environment variables**

Service → Variables → add every var under "Railway (backend)" in `docs/deploy/PROD_ENV.md`, using the Supabase keys from Task 2. For `APP_BASE_URL` put a placeholder for now (corrected in Task 5).

- [ ] **Step 3: Generate a public domain**

Service → Settings → Networking → Generate Domain. Record it as `<railway-service>.up.railway.app`. Optionally set Healthcheck Path = `/health`.

- [ ] **Step 4: Deploy & verify health** (🤖 can run this once the URL exists)

```bash
curl -s https://<railway-service>.up.railway.app/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 5: Verify trending endpoint (may be empty until first scheduler run)**

```bash
curl -s https://<railway-service>.up.railway.app/trending
```
Expected: JSON `{"generated_at": ..., "cards": [...]}`. If `cards` is empty, the daily trending pass hasn't run yet — either wait until `TRENDING_REFRESH_UTC`, or temporarily set `TRENDING_REFRESH_UTC` to a minute a few minutes out, redeploy, and re-check.

---

### Task 4: Vercel — deploy the web app 🧑 (🤖 verifies)

**Files:** none (Vercel auto-detects Next.js)

- [ ] **Step 1: Import the project**

At <https://vercel.com> → Add New → Project → import this GitHub repo. Set **Root Directory = `web`**. Framework preset auto-detects as Next.js. Leave build settings default.

- [ ] **Step 2: Set environment variables**

Add every var under "Vercel (web)" in `docs/deploy/PROD_ENV.md`. Set `DISTILL_API_URL` to the Railway domain from Task 3. Set `NEXT_PUBLIC_DEMO_MODE=false`.

- [ ] **Step 3: Deploy**

Click Deploy. Record the production URL `https://<app>.vercel.app`.

- [ ] **Step 4: Verify the front page renders (real backend, not demo)** (🤖)

```bash
curl -s https://<app>.vercel.app/ | grep -o "Today, distilled" | head -1
```
Expected: `Today, distilled` (the public trending front page renders). Note: with a real backend and an empty trending table, cards may be sparse until Task 3 Step 5 succeeds.

---

### Task 5: Wire auth redirect URLs 🧑

**Files:** none (Supabase + Railway dashboards)

- [ ] **Step 1: Point Supabase auth at the Vercel URL**

Supabase → Authentication → URL Configuration:
- Site URL = `https://<app>.vercel.app`
- Redirect allowlist add = `https://<app>.vercel.app/auth/callback`

- [ ] **Step 2: Correct `APP_BASE_URL` on Railway**

Railway → Variables → set `APP_BASE_URL=https://<app>.vercel.app` (the digest email's "Open in Distill" link). Redeploy if it doesn't auto-redeploy.

- [ ] **Step 3: Verify sign-in end-to-end** 🧑

Open `https://<app>.vercel.app`, click Sign in, enter your email, click the magic link in your inbox. Expected: you land signed in, on the blend (Your Digest + Trending). (At low volume this uses Supabase's built-in email; deliverability improves in Phase 2.)

---

### Task 6: End-to-end production verification 🧑 (🤖 assists)

- [ ] **Step 1: Trending visible logged-out**

Visit `/` in a private window → trending cards render without sign-in.

- [ ] **Step 2: Follow flow**

Signed in, click **+ Follow** on a trending card → it moves into Your Digest (after revalidate/refresh).

- [ ] **Step 3: Add a custom topic**

Topics tab → add a topic (3–60 chars) → appears; the 11th add is blocked.

- [ ] **Step 4: Digest generation**

Confirm a per-user digest exists: visit `/` signed in and see Your Digest populate (generation runs on your delivery time; you can also confirm via the backend logs that the scheduler ticks).

- [ ] **Step 5: Confirm auto-deploy**

Push a trivial change to `main` → confirm Vercel and Railway both rebuild automatically.

---

### Task 7 (Phase 2, when ready): Domain + real email 🧑

**Files:** none (registrar DNS + Resend + Supabase + Vercel dashboards)

- [ ] **Step 1: Buy a domain** (~$12/yr) at any registrar.

- [ ] **Step 2: Verify it in Resend**

Resend → Domains → Add domain → add the SPF/DKIM DNS records it gives you at your registrar. Wait for "Verified".

- [ ] **Step 3: Point the sender at your domain**

Railway → set `RESEND_FROM_EMAIL=digest@yourdomain.com`. Redeploy.

- [ ] **Step 4 (recommended): Use Resend as Supabase's SMTP**

Supabase → Project Settings → Auth → SMTP Settings → enter Resend SMTP credentials and a `from` on your domain. This makes magic-link emails deliverable at volume.

- [ ] **Step 5 (optional): Move the app to your domain**

Vercel → Domains → add your domain. Then update `APP_BASE_URL` (Railway), Supabase Site URL + redirect allowlist, and `NEXT_PUBLIC_*`/`DISTILL_API_URL` as needed to the new URLs.

- [ ] **Step 6: Verify real email**

Sign up a second test account on a different email provider → confirm the magic link and the daily digest arrive in the inbox (not spam).

---

## Self-Review

**Spec coverage:**
- Topology (Vercel/Railway/Supabase/Resend): Tasks 2–4 ✓
- CI/CD git-driven, root dirs: Tasks 3 (root `backend`), 4 (root `web`), 6 Step 5 ✓
- Config & secrets (exact env vars per platform): Task 1 Step 2 + Tasks 3/4 ✓
- Supabase auth URL configuration: Task 5 ✓
- Migrations in order: Task 2 Step 2 ✓
- Phased email path (Phase 1 free, Phase 2 domain): Phase 1 across Tasks 2–6; Phase 2 = Task 7 ✓
- Verification steps: Tasks 3/4/5/6 ✓
- Always-on backend / no sleep: Railway service (Task 3), not a sleeping free tier ✓
- No CORS: not needed (BFF proxies) — no task required, correct ✓

**Placeholder scan:** Bracketed values like `<project>`, `<app>`, `<railway-service>` are intentional fill-ins the human substitutes from their own dashboards, not plan placeholders. No "TBD"/"TODO" remain.

**Consistency:** Env var names match across `PROD_ENV.md`, the Railway/Vercel tasks, and the backend code (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `ANTHROPIC_API_KEY`, `EXA_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `APP_BASE_URL`, `TRENDING_REFRESH_UTC`, `NEXT_PUBLIC_DEMO_MODE`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `DISTILL_API_URL`). Root directories (`web`, `backend`) match the repo layout and the Procfile.
