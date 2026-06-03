---
name: project-state
description: Current implementation state of Distill as of 2026-06-03
metadata:
  node_type: memory
  type: project
  originSessionId: a2153663-3ad8-4105-be63-9948d7edb810
---

Nearly complete. All backend modules and almost all iOS slices are done. One slice blocked on Firebase.

**Backend (35 tests, all passing):**
- `synthesis_engine.py`, `digest_orchestrator.py`, `scheduler_worker.py`, `push_notification_service.py`, `api.py`
- Auth middleware validates Supabase Bearer JWTs (PyJWT + SUPABASE_JWT_SECRET)
- Endpoints: topic CRUD, digest get/generate, single-card refresh (rate-limited 60 min), settings

**iOS (builds clean on iPhone 16 simulator):**
- Auth: Sign in with Apple via Supabase, session persisted in Keychain
- Topics tab: full CRUD, drag-to-reorder, swipe-delete, 10-topic cap, Settings sheet (delivery time + sign out)
- Digest tab: TopicCard list (tldr, bullets, tappable sources via SFSafariViewController), pull-to-refresh, per-card refresh button, error state + retry
- Onboarding wizard: 3-screen (sign in → add topics → delivery time), auto-generates first digest on completion
- Offline cache: OfflineCacheModule (Documents/digest_cache.json), NetworkMonitor, "Offline — last updated" banner

**Closed GitHub issues:** #2, #3, #4, #5, #6, #7, #8, #9, #10, #12, #13, #14

**Remaining open:**
- **#11** (Push notifications): Blocked — Firebase project not set up (HITL). Needs Firebase console setup, GoogleService-Info.plist, APNs key upload to Firebase.

**Credentials in .env (gitignored):**
- Supabase URL, anon key, service role key, JWT secret
- Anthropic API key, Exa.ai API key

**Why:** Firebase setup is HITL — requires Apple Developer portal + Firebase console interaction before push notifications can be wired up.

**How to apply:** Next session starts at issue #11. Before suggesting Firebase work, confirm Gaurav has set up Firebase project + uploaded APNs key.
