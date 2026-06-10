# Distill Web — Backend (Email + Timezone) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace FCM push delivery with Resend email delivery and make Delivery Time timezone-aware, with no change to the synthesis/orchestration pipeline.

**Architecture:** A new `EmailDigestService` renders the Digest as HTML and sends it through a thin `ResendClient` adapter. The `SchedulerWorker`'s injected notifier is swapped from push to email. Delivery-time matching moves from UTC-only to per-user timezone via a pure `user_is_due()` function. The iOS-only push stack (`PushNotificationService`, `firebase_client`) is removed.

**Tech Stack:** Python 3.13, FastAPI, pytest, httpx, Supabase (PostgreSQL), Resend.

**Scope note:** This plan is the backend half of the `2026-06-10-distill-web-design.md` spec. The Next.js client is a separate plan. After this plan, the backend still serves the existing REST API unchanged and the 34 non-push tests stay green.

**Assumptions:**
- The Supabase `users` table has (or will have) an `email` column populated from Supabase Auth. Task 1 adds `timezone`; `email` is assumed present. If it is not, add it in the same migration.
- `digest` passed to the notifier is the `Digest` dataclass from `DigestOrchestrator.generate` (`topic_cards: list[TopicCardResult]`), each `TopicCardResult` having `.topic_id`, `.status`, and `.card` (a `TopicCard` with `.tldr`, `.bullets`, `.sources` where each source has `.title`/`.url`), per `digest_orchestrator.py` and `synthesis_engine.py`.

---

### Task 1: Add `timezone` column to the users table

**Files:**
- Create: `supabase/migrations/20260610000000_add_user_timezone.sql`

- [ ] **Step 1: Write the migration**

```sql
-- Add per-user timezone for Delivery Time matching (web has no device-local time).
alter table public.users
  add column if not exists timezone text not null default 'UTC';
```

- [ ] **Step 2: Apply locally (if Supabase CLI is available) or note for manual apply**

Run: `supabase db push` (or paste the SQL into the Supabase SQL editor).
Expected: column `timezone` exists on `public.users` with default `'UTC'`.

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/20260610000000_add_user_timezone.sql
git commit -m "feat(db): add timezone column to users"
```

---

### Task 2: `ResendClient` adapter

**Files:**
- Create: `backend/src/distill/resend_client.py`
- Test: `backend/tests/test_resend_client.py`

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import MagicMock
from distill.resend_client import ResendClient


def test_send_posts_to_resend_with_auth_and_payload():
    http = MagicMock()
    http.post.return_value = MagicMock(
        status_code=200, json=lambda: {"id": "email-1"}
    )
    client = ResendClient(
        api_key="re_test", from_email="digest@distill.app", http_client=http
    )

    result = client.send(
        to="maya@example.com", subject="Your Distill digest", html="<p>hi</p>"
    )

    assert result == {"id": "email-1"}
    http.post.assert_called_once_with(
        "https://api.resend.com/emails",
        headers={"Authorization": "Bearer re_test"},
        json={
            "from": "digest@distill.app",
            "to": ["maya@example.com"],
            "subject": "Your Distill digest",
            "html": "<p>hi</p>",
        },
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_resend_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'distill.resend_client'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Thin Resend HTTP API adapter for sending Digest emails."""
from __future__ import annotations


class ResendClient:
    _ENDPOINT = "https://api.resend.com/emails"

    def __init__(self, api_key: str, from_email: str, http_client=None):
        self._api_key = api_key
        self._from_email = from_email
        if http_client is None:
            import httpx
            http_client = httpx.Client(timeout=10.0)
        self._http = http_client

    def send(self, to: str, subject: str, html: str) -> dict:
        resp = self._http.post(
            self._ENDPOINT,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "from": self._from_email,
                "to": [to],
                "subject": subject,
                "html": html,
            },
        )
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_resend_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/distill/resend_client.py backend/tests/test_resend_client.py
git commit -m "feat(email): add ResendClient adapter"
```

---

### Task 3: `EmailDigestService` — subject formatting

**Files:**
- Create: `backend/src/distill/email_digest_service.py`
- Test: `backend/tests/test_email_digest_service.py`

The subject reuses the personalised "Topic names + N more" shape from the old push body.

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import MagicMock
from distill.email_digest_service import EmailDigestService


def make_service(recipient):
    email_client = MagicMock()
    service = EmailDigestService(
        email_client=email_client,
        fetch_recipient=lambda user_id: recipient,
        app_base_url="https://distill.app",
    )
    return service, email_client


def test_subject_single_topic():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )

    service.send("user-1", digest=_empty_digest())

    subject = client.send.call_args.kwargs["subject"]
    assert subject == "Your Distill digest — Fed policy"


def test_subject_three_topics_truncates():
    service, client = make_service(
        {
            "email": "maya@example.com",
            "topic_phrases": ["Fed policy", "Space", "Watches"],
        }
    )

    service.send("user-1", digest=_empty_digest())

    subject = client.send.call_args.kwargs["subject"]
    assert subject == "Your Distill digest — Fed policy, Space +1 more"


def _empty_digest():
    from distill.digest_orchestrator import Digest
    return Digest(topic_cards=[])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_email_digest_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'distill.email_digest_service'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Renders a Digest as HTML email and sends it via an injected email client."""
from __future__ import annotations

from distill.digest_orchestrator import Digest


class EmailDigestService:
    _SUBJECT_PREFIX = "Your Distill digest"

    def __init__(self, email_client, fetch_recipient, app_base_url: str):
        self._email_client = email_client
        self._fetch_recipient = fetch_recipient
        self._app_base_url = app_base_url

    def send(self, user_id: str, digest: Digest) -> None:
        recipient = self._fetch_recipient(user_id) or {}
        email = recipient.get("email")
        if not email:
            return
        topic_phrases = recipient.get("topic_phrases", [])
        self._email_client.send(
            to=email,
            subject=self._format_subject(topic_phrases),
            html=self._render_html(digest),
        )

    def _format_subject(self, topic_phrases: list[str]) -> str:
        n = len(topic_phrases)
        if n == 0:
            return self._SUBJECT_PREFIX
        if n == 1:
            return f"{self._SUBJECT_PREFIX} — {topic_phrases[0]}"
        if n == 2:
            return f"{self._SUBJECT_PREFIX} — {topic_phrases[0]}, {topic_phrases[1]}"
        remainder = n - 2
        return (
            f"{self._SUBJECT_PREFIX} — {topic_phrases[0]}, {topic_phrases[1]}"
            f" +{remainder} more"
        )

    def _render_html(self, digest: Digest) -> str:
        return ""  # filled in Task 4
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_email_digest_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/distill/email_digest_service.py backend/tests/test_email_digest_service.py
git commit -m "feat(email): EmailDigestService subject formatting"
```

---

### Task 4: `EmailDigestService` — HTML body rendering

**Files:**
- Modify: `backend/src/distill/email_digest_service.py`
- Test: `backend/tests/test_email_digest_service.py`

- [ ] **Step 1: Write the failing tests**

```python
def _ok_digest():
    from distill.digest_orchestrator import Digest, TopicCardResult
    from distill.synthesis_engine import TopicCard, Source

    card = TopicCard(
        tldr="Rates held steady.",
        bullets=["No hike", "Dovish tone"],
        sources=[Source(title="Fed statement", url="https://fed.gov/x")],
    )
    return Digest(topic_cards=[TopicCardResult(topic_id="t1", card=card, status="ok")])


def _error_digest():
    from distill.digest_orchestrator import Digest, TopicCardResult
    return Digest(topic_cards=[TopicCardResult(topic_id="t1", card=None, status="error")])


def test_html_includes_tldr_bullets_and_source():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )

    service.send("user-1", digest=_ok_digest())

    html = client.send.call_args.kwargs["html"]
    assert "Rates held steady." in html
    assert "No hike" in html
    assert "Dovish tone" in html
    assert "https://fed.gov/x" in html


def test_html_includes_open_in_distill_link():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )

    service.send("user-1", digest=_ok_digest())

    html = client.send.call_args.kwargs["html"]
    assert "https://distill.app" in html
    assert "Open in Distill" in html


def test_html_renders_error_state_for_failed_card():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )

    service.send("user-1", digest=_error_digest())

    html = client.send.call_args.kwargs["html"]
    assert "couldn’t be generated" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest backend/tests/test_email_digest_service.py -v`
Expected: FAIL — the three new tests fail on missing strings (empty HTML).

- [ ] **Step 3: Implement `_render_html`**

(Source type confirmed: `synthesis_engine.Source(title: str, url: str)`, and `TopicCard(tldr, bullets, sources)`.)

Replace the `_render_html` stub:

```python
    def _render_html(self, digest: Digest) -> str:
        sections = [self._render_card(c) for c in digest.topic_cards]
        button = (
            f'<p><a href="{self._app_base_url}" '
            f'style="display:inline-block;padding:10px 16px;background:#111;'
            f'color:#fff;text-decoration:none;border-radius:6px">'
            f"Open in Distill</a></p>"
        )
        return f"<div>{''.join(sections)}{button}</div>"

    def _render_card(self, result) -> str:
        if result.status != "ok" or result.card is None:
            return (
                "<section><p><em>This Topic Card couldn’t be generated. "
                "Open Distill to retry.</em></p></section>"
            )
        card = result.card
        bullets = "".join(f"<li>{b}</li>" for b in card.bullets)
        sources = "".join(
            f'<li><a href="{s.url}">{s.title}</a></li>' for s in card.sources
        )
        return (
            "<section>"
            f"<h2>{card.tldr}</h2>"
            f"<ul>{bullets}</ul>"
            f"<p>Sources:</p><ul>{sources}</ul>"
            "</section>"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest backend/tests/test_email_digest_service.py -v`
Expected: PASS (all subject + HTML tests)

- [ ] **Step 5: Add the no-email guard test**

```python
def test_no_email_does_not_send():
    service, client = make_service({"email": None, "topic_phrases": ["Fed policy"]})

    service.send("user-1", digest=_ok_digest())

    client.send.assert_not_called()
```

Run: `python3 -m pytest backend/tests/test_email_digest_service.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/distill/email_digest_service.py backend/tests/test_email_digest_service.py
git commit -m "feat(email): render Digest HTML with sources, deep link, error state"
```

---

### Task 5: Timezone-aware `user_is_due()`

**Files:**
- Create: `backend/src/distill/scheduling.py`
- Test: `backend/tests/test_scheduling.py`

- [ ] **Step 1: Write the failing tests**

```python
from datetime import datetime, timezone
from distill.scheduling import user_is_due


def test_due_when_local_time_matches_delivery_time():
    # 11:00 UTC == 07:00 America/New_York (EDT, summer)
    now = datetime(2026, 6, 10, 11, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00", tz_name="America/New_York") is True


def test_not_due_when_local_time_differs():
    now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00", tz_name="America/New_York") is False


def test_handles_seconds_suffix_in_delivery_time():
    now = datetime(2026, 6, 10, 11, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00:00", tz_name="America/New_York") is True


def test_unknown_timezone_falls_back_to_utc():
    now = datetime(2026, 6, 10, 7, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="07:00", tz_name="Not/AZone") is True


def test_empty_delivery_time_is_not_due():
    now = datetime(2026, 6, 10, 7, 0, tzinfo=timezone.utc)
    assert user_is_due(now, delivery_time="", tz_name="UTC") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest backend/tests/test_scheduling.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'distill.scheduling'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Pure Delivery-Time matching logic, timezone-aware."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def user_is_due(now_utc: datetime, delivery_time: str, tz_name: str) -> bool:
    if not delivery_time:
        return False
    try:
        tz = ZoneInfo(tz_name or "UTC")
    except Exception:
        tz = ZoneInfo("UTC")
    local_hhmm = now_utc.astimezone(tz).strftime("%H:%M")
    return local_hhmm == delivery_time[:5]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest backend/tests/test_scheduling.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/distill/scheduling.py backend/tests/test_scheduling.py
git commit -m "feat(scheduler): timezone-aware user_is_due()"
```

---

### Task 6: Rename the SchedulerWorker notifier to `email_service`

**Files:**
- Modify: `backend/src/distill/scheduler_worker.py`
- Test: `backend/tests/test_scheduler_worker.py`

- [ ] **Step 1: Update the test to use `email_service`**

In `backend/tests/test_scheduler_worker.py`, rename the stub and constructor kwarg. Replace the `StubPushService` class and the `SchedulerWorker(...)` construction inside `make_worker`:

```python
    class StubEmailService:
        def send(self, user_id, digest):
            if push_calls is not None:
                push_calls.append((user_id, digest))

    _persist_calls = persist_calls if persist_calls is not None else []

    def persist_digest(user_id, digest):
        _persist_calls.append((user_id, digest))

    return SchedulerWorker(
        fetch_due_users=fetch_due_users,
        orchestrator=StubOrchestrator(),
        persist_digest=persist_digest,
        email_service=StubEmailService(),
    ), _persist_calls
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest backend/tests/test_scheduler_worker.py -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'email_service'`

- [ ] **Step 3: Rename the parameter in the implementation**

Replace `backend/src/distill/scheduler_worker.py` entirely:

```python
class SchedulerWorker:
    def __init__(self, fetch_due_users, orchestrator, persist_digest, email_service):
        self._fetch_due_users = fetch_due_users
        self._orchestrator = orchestrator
        self._persist_digest = persist_digest
        self._email_service = email_service

    def tick(self):
        user_ids = self._fetch_due_users()
        for user_id in user_ids:
            try:
                digest = self._orchestrator.generate(user_id)
                self._persist_digest(user_id, digest)
                self._email_service.send(user_id, digest)
            except Exception:
                continue
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest backend/tests/test_scheduler_worker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/distill/scheduler_worker.py backend/tests/test_scheduler_worker.py
git commit -m "refactor(scheduler): rename notifier to email_service"
```

---

### Task 7: Expose `timezone` through `SupabaseDb` settings

**Files:**
- Modify: `backend/src/distill/supabase_db.py:104-111`
- Test: `backend/tests/test_supabase_db.py` (create)

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import MagicMock
from distill.supabase_db import SupabaseDb


def _chain_returning(rows):
    """Build a Supabase query-builder mock whose execute() returns rows."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.execute.return_value = MagicMock(data=rows)
    return chain


def test_get_settings_selects_timezone():
    chain = _chain_returning(
        [{"delivery_time": "07:00", "device_token": None, "timezone": "America/New_York"}]
    )
    client = MagicMock()
    client.table.return_value = chain

    settings = SupabaseDb(client).get_settings("user-1")

    chain.select.assert_called_once_with("delivery_time, device_token, timezone")
    assert settings["timezone"] == "America/New_York"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest backend/tests/test_supabase_db.py -v`
Expected: FAIL — `select` called with `"delivery_time, device_token"` (missing `timezone`).

- [ ] **Step 3: Update the select**

In `backend/src/distill/supabase_db.py`, change the `get_settings` select string:

```python
    def get_settings(self, user_id: str) -> dict:
        result = (
            self._db.table("users")
            .select("delivery_time, device_token, timezone")
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest backend/tests/test_supabase_db.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/distill/supabase_db.py backend/tests/test_supabase_db.py
git commit -m "feat(db): expose timezone in settings"
```

---

### Task 8: Rewire `main.py` to email + timezone, remove push stack

**Files:**
- Modify: `backend/src/distill/main.py`
- Delete: `backend/src/distill/push_notification_service.py`
- Delete: `backend/src/distill/firebase_client.py`
- Delete: `backend/tests/test_push_notification_service.py`

No unit test for wiring itself (it is integration glue exercised by the deployed worker); correctness of the pieces is covered by Tasks 2–7. After editing, the import-smoke check in Step 4 guards against breakage.

- [ ] **Step 1: Replace the imports and `_build_scheduler`**

In `backend/src/distill/main.py`, replace the push/firebase imports:

```python
from distill.email_digest_service import EmailDigestService
from distill.resend_client import ResendClient
from distill.scheduling import user_is_due
```

(remove `from distill.firebase_client import FirebaseFCMClient` and
`from distill.push_notification_service import PushNotificationService`.)

Replace `_build_scheduler` with:

```python
def _build_scheduler(supabase, orchestrator) -> SchedulerWorker:
    from distill.supabase_db import SupabaseDb
    db = SupabaseDb(supabase)

    resend = ResendClient(
        api_key=os.environ["RESEND_API_KEY"],
        from_email=os.environ["RESEND_FROM_EMAIL"],
    )

    def fetch_recipient(user_id: str) -> dict:
        row = (
            supabase.table("users")
            .select("email")
            .eq("id", user_id)
            .execute()
        )
        email = row.data[0]["email"] if row.data else None
        topic_phrases = [t["phrase"] for t in db.get_topics(user_id)]
        return {"email": email, "topic_phrases": topic_phrases}

    email_service = EmailDigestService(
        email_client=resend,
        fetch_recipient=fetch_recipient,
        app_base_url=os.environ.get("APP_BASE_URL", "https://distill.app"),
    )

    def fetch_due_users():
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        result = supabase.table("users").select("id, delivery_time, timezone").execute()
        return [
            row["id"]
            for row in (result.data or [])
            if user_is_due(now, row.get("delivery_time", ""), row.get("timezone", "UTC"))
        ]

    def persist_digest(user_id: str, digest):
        db.save_digest(user_id, digest)

    return SchedulerWorker(
        fetch_due_users=fetch_due_users,
        orchestrator=orchestrator,
        persist_digest=persist_digest,
        email_service=email_service,
    )
```

- [ ] **Step 2: Delete the push/firebase modules and test**

```bash
git rm backend/src/distill/push_notification_service.py \
       backend/src/distill/firebase_client.py \
       backend/tests/test_push_notification_service.py
```

- [ ] **Step 3: Confirm no lingering references**

Run: `grep -rn "push_notification_service\|FirebaseFCMClient\|PushNotificationService\|firebase_client" backend/`
Expected: no output.

- [ ] **Step 4: Smoke-test the import**

Run: `cd backend && python3 -c "import distill.main"`
Expected: no error (module imports cleanly).

- [ ] **Step 5: Commit**

```bash
git add backend/src/distill/main.py
git commit -m "feat: wire email delivery + timezone scheduling, remove push stack"
```

---

### Task 9: Update environment template

**Files:**
- Modify: `backend/.env.example` (or repo-root `.env.example` — use whichever the repo already has)

- [ ] **Step 1: Edit the example env**

Remove `FIREBASE_SERVICE_ACCOUNT`. Add:

```
# Email delivery (Resend)
RESEND_API_KEY=
RESEND_FROM_EMAIL=digest@distill.app
# Base URL the digest email links back to
APP_BASE_URL=https://distill.app
```

- [ ] **Step 2: Commit**

```bash
git add .env.example backend/.env.example 2>/dev/null; git commit -m "chore: env example for Resend, drop Firebase"
```

---

### Task 10: Full suite green + dependency check

**Files:** none (verification)

- [ ] **Step 1: Ensure `httpx` is a declared dependency**

Check `backend/pyproject.toml` (or `requirements.txt`). If `httpx` is not listed, add it (it is already transitively present via Supabase/Starlette, but declare it explicitly for `ResendClient`).

- [ ] **Step 2: Run the whole backend suite**

Run: `cd backend && python3 -m pytest -q`
Expected: PASS, with the push test gone and `test_resend_client`, `test_email_digest_service`, `test_scheduling`, `test_supabase_db` added. Net: 34 prior non-push tests + new tests, 0 failures.

- [ ] **Step 3: Commit any dependency change**

```bash
git add backend/pyproject.toml backend/requirements.txt 2>/dev/null; git commit -m "chore: declare httpx dependency" || echo "nothing to commit"
```

---

## Self-Review

**Spec coverage:**
- Replace `PushNotificationService` → `EmailDigestService` (Resend): Tasks 2–4, 8 ✓
- Email contains Topic Cards + "Open in Distill" deep link + error state: Task 4 ✓
- Timezone field + timezone-aware Delivery Time matching: Tasks 1, 5, 7, 8 ✓
- Email test replaces push test, suite stays green: Tasks 3, 4, 8, 10 ✓
- Env: add `RESEND_API_KEY`, drop `FIREBASE_SERVICE_ACCOUNT`: Task 9 ✓
- Backend REST surface otherwise unchanged: no API task — confirmed unchanged ✓
- ADR-0003 + CONTEXT.md doc updates: **belong to the frontend/docs plan**, noted here so they are not lost.

**Type consistency:** `EmailDigestService(email_client, fetch_recipient, app_base_url)` and its `.send(user_id, digest)` are used identically in Tasks 3, 4, and the Task 8 wiring. `ResendClient.send(to, subject, html)` matches the call in `EmailDigestService.send`. `user_is_due(now_utc, delivery_time, tz_name)` signature matches its use in Task 8. The scheduler kwarg `email_service=` matches in Tasks 6 and 8.

**Placeholder scan:** No TBD/TODO remain. Source/TopicCard type names were verified against `synthesis_engine.py` (`Source(title, url)`, `TopicCard(tldr, bullets, sources)`).
