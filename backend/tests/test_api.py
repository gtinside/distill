"""API layer tests — one behavior per RED→GREEN cycle."""
import pytest
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------

class StubDb:
    """In-memory stub for the Supabase db dependency."""

    def __init__(self):
        self.topics: list[dict] = []
        self.digest: dict | None = None
        self.settings: dict = {"delivery_time": "08:00"}

    # Topics ------------------------------------------------------------------

    def get_topics(self, user_id: str) -> list[dict]:
        return sorted(
            [t for t in self.topics if t["user_id"] == user_id],
            key=lambda t: t.get("display_order", 0),
        )

    def count_topics(self, user_id: str) -> int:
        return len([t for t in self.topics if t["user_id"] == user_id])

    def create_topic(self, user_id: str, phrase: str) -> dict:
        topic = {
            "id": f"topic-{len(self.topics)+1}",
            "user_id": user_id,
            "phrase": phrase,
            "display_order": len(self.topics),
        }
        self.topics.append(topic)
        return topic

    def get_topic(self, topic_id: str) -> dict | None:
        return next((t for t in self.topics if t["id"] == topic_id), None)

    def update_topic(self, topic_id: str, data: dict) -> dict:
        for t in self.topics:
            if t["id"] == topic_id:
                t.update(data)
                return t
        return None

    def delete_topic(self, topic_id: str) -> None:
        self.topics[:] = [t for t in self.topics if t["id"] != topic_id]

    # Digest ------------------------------------------------------------------

    def get_digest(self, user_id: str) -> dict | None:
        return self.digest

    def save_digest(self, user_id: str, digest: dict) -> dict:
        self.digest = digest
        return digest

    def get_topic_card(self, user_id: str, topic_id: str) -> dict | None:
        if not self.digest:
            return None
        return next(
            (c for c in self.digest.get("topic_cards", []) if c.get("topic_id") == topic_id),
            None,
        )

    def update_topic_card(self, card_id: str, data: dict) -> dict:
        if self.digest:
            for card in self.digest.get("topic_cards", []):
                if card.get("id") == card_id:
                    card.update(data)
                    return card
        return data

    # Settings ----------------------------------------------------------------

    def get_settings(self, user_id: str) -> dict:
        return self.settings

    def update_settings(self, user_id: str, data: dict) -> dict:
        self.settings.update(data)
        return self.settings


class StubOrchestrator:
    """In-memory stub for DigestOrchestrator."""

    def __init__(self, result=None, refresh_result=None):
        from distill.digest_orchestrator import Digest, TopicCardResult
        self.called_generate_with: str | None = None
        self.called_refresh_with = None
        self._result = result or Digest(topic_cards=[])
        self._refresh_result = refresh_result or TopicCardResult(
            topic_id="topic-1", card=None, status="ok"
        )

    def generate(self, user_id: str):
        self.called_generate_with = user_id
        return self._result

    def refresh_card(self, topic_id: str, phrase: str):
        self.called_refresh_with = (topic_id, phrase)
        return self._refresh_result


# ---------------------------------------------------------------------------
# Client factory — used by every test
# ---------------------------------------------------------------------------

TEST_JWT_SECRET = "test-secret"


def make_client(db=None, orchestrator=None) -> TestClient:
    from distill.api import create_app
    app = create_app(db=db or StubDb(), orchestrator=orchestrator or StubOrchestrator())
    return TestClient(app, raise_server_exceptions=True)


def make_jwt(user_id: str) -> str:
    import jwt
    return jwt.encode({"sub": user_id}, TEST_JWT_SECRET, algorithm="HS256")


def make_authed_client(db=None, orchestrator=None) -> TestClient:
    from distill.api import create_app
    app = create_app(
        db=db or StubDb(),
        orchestrator=orchestrator or StubOrchestrator(),
        jwt_secret=TEST_JWT_SECRET,
    )
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Behavior 1: POST /topics — valid phrase → 201, topic created in db
# ---------------------------------------------------------------------------

def test_create_topic_valid_phrase():
    db = StubDb()
    client = make_client(db=db)

    resp = client.post(
        "/topics",
        json={"phrase": "machine learning"},
        headers={"X-User-Id": "user-1"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["phrase"] == "machine learning"
    assert body["user_id"] == "user-1"
    # Also persisted in db
    assert db.count_topics("user-1") == 1


# ---------------------------------------------------------------------------
# Behavior 2: POST /topics — phrase too short (< 3 chars) → 422
# ---------------------------------------------------------------------------

def test_create_topic_phrase_too_short():
    client = make_client()
    resp = client.post(
        "/topics",
        json={"phrase": "ab"},
        headers={"X-User-Id": "user-1"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Behavior 3: POST /topics — phrase too long (> 60 chars) -> 422
# ---------------------------------------------------------------------------

def test_create_topic_phrase_too_long():
    client = make_client()
    long_phrase = "a" * 61
    resp = client.post(
        "/topics",
        json={"phrase": long_phrase},
        headers={"X-User-Id": "user-1"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Behavior 4: POST /topics — user already has 10 topics -> 422
# ---------------------------------------------------------------------------

def test_create_topic_at_limit():
    db = StubDb()
    client = make_client(db=db)

    # Pre-populate 10 topics for user-1
    for i in range(10):
        db.create_topic("user-1", f"topic phrase {i}")

    resp = client.post(
        "/topics",
        json={"phrase": "eleventh topic"},
        headers={"X-User-Id": "user-1"},
    )
    assert resp.status_code == 422
    assert db.count_topics("user-1") == 10  # no new topic added


# ---------------------------------------------------------------------------
# Behavior 5: GET /topics -> 200, list ordered by display_order
# ---------------------------------------------------------------------------

def test_list_topics_ordered_by_display_order():
    db = StubDb()
    # Insert out-of-order display_orders
    db.topics = [
        {"id": "t1", "user_id": "user-1", "phrase": "second", "display_order": 2},
        {"id": "t2", "user_id": "user-1", "phrase": "first",  "display_order": 1},
        {"id": "t3", "user_id": "user-1", "phrase": "third",  "display_order": 3},
    ]
    client = make_client(db=db)

    resp = client.get("/topics", headers={"X-User-Id": "user-1"})

    assert resp.status_code == 200
    phrases = [t["phrase"] for t in resp.json()]
    assert phrases == ["first", "second", "third"]


# ---------------------------------------------------------------------------
# Behavior 6: DELETE /topics/{id} -> 204, topic removed
# ---------------------------------------------------------------------------

def test_delete_topic():
    db = StubDb()
    db.topics = [{"id": "t99", "user_id": "user-1", "phrase": "to delete", "display_order": 0}]
    client = make_client(db=db)

    resp = client.delete("/topics/t99", headers={"X-User-Id": "user-1"})

    assert resp.status_code == 204
    assert db.count_topics("user-1") == 0


# ---------------------------------------------------------------------------
# Behavior 7: GET /digest -> 200, returns digest from db
# ---------------------------------------------------------------------------

def test_get_digest():
    db = StubDb()
    db.digest = {"topic_cards": [{"topic_id": "t1", "status": "ok"}]}
    client = make_client(db=db)

    resp = client.get("/digest", headers={"X-User-Id": "user-1"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["topic_cards"][0]["topic_id"] == "t1"


# ---------------------------------------------------------------------------
# Behavior 8: POST /digest/generate -> 200, orchestrator called, digest returned
# ---------------------------------------------------------------------------

def test_generate_digest():
    from distill.digest_orchestrator import Digest, TopicCardResult
    result = Digest(topic_cards=[TopicCardResult(topic_id="t42", card=None, status="ok")])
    orchestrator = StubOrchestrator(result=result)
    client = make_client(orchestrator=orchestrator)

    resp = client.post("/digest/generate", headers={"X-User-Id": "user-99"})

    assert resp.status_code == 200
    assert resp.json()["topic_cards"][0]["topic_id"] == "t42"
    assert orchestrator.called_generate_with == "user-99"


# ---------------------------------------------------------------------------
# Behavior 9: PATCH /settings — valid delivery_time -> 200
# ---------------------------------------------------------------------------

def test_patch_settings_delivery_time():
    db = StubDb()
    client = make_client(db=db)

    resp = client.patch(
        "/settings",
        json={"delivery_time": "07:30"},
        headers={"X-User-Id": "user-1"},
    )

    assert resp.status_code == 200
    assert resp.json()["delivery_time"] == "07:30"
    assert db.settings["delivery_time"] == "07:30"


# ---------------------------------------------------------------------------
# Behavior 10: Any endpoint without auth header -> 401
# ---------------------------------------------------------------------------

def test_missing_auth_header_returns_401():
    client = make_client()

    endpoints = [
        ("GET",    "/topics"),
        ("POST",   "/topics"),
        ("DELETE", "/topics/some-id"),
        ("GET",    "/digest"),
        ("POST",   "/digest/generate"),
        ("PATCH",  "/settings"),
    ]

    for method, path in endpoints:
        resp = client.request(method, path)
        assert resp.status_code == 401, (
            f"Expected 401 for {method} {path}, got {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# Behavior 11: PATCH /topics/:id — valid update returns updated topic
# ---------------------------------------------------------------------------

def test_patch_topic_phrase():
    db = StubDb()
    db.topics = [{"id": "t1", "user_id": "user-1", "phrase": "original", "display_order": 0}]
    client = make_client(db=db)

    resp = client.patch(
        "/topics/t1",
        json={"phrase": "updated phrase"},
        headers={"X-User-Id": "user-1"},
    )

    assert resp.status_code == 200
    assert resp.json()["phrase"] == "updated phrase"


# ---------------------------------------------------------------------------
# Behavior 12: PATCH /topics/:id — another user's topic -> 403
# ---------------------------------------------------------------------------

def test_patch_topic_forbidden():
    db = StubDb()
    db.topics = [{"id": "t1", "user_id": "user-1", "phrase": "private", "display_order": 0}]
    client = make_client(db=db)

    resp = client.patch(
        "/topics/t1",
        json={"phrase": "hijacked"},
        headers={"X-User-Id": "user-2"},
    )

    assert resp.status_code == 403
    assert db.get_topic("t1")["phrase"] == "private"  # unchanged


# ---------------------------------------------------------------------------
# Behavior 13: DELETE /topics/:id — another user's topic -> 403
# ---------------------------------------------------------------------------

def test_delete_topic_forbidden():
    db = StubDb()
    db.topics = [{"id": "t1", "user_id": "user-1", "phrase": "private", "display_order": 0}]
    client = make_client(db=db)

    resp = client.delete("/topics/t1", headers={"X-User-Id": "user-2"})

    assert resp.status_code == 403
    assert db.count_topics("user-1") == 1  # not deleted


# ---------------------------------------------------------------------------
# Behavior 14: Valid Bearer JWT -> authenticated, user_id extracted from sub claim
# ---------------------------------------------------------------------------

def test_bearer_jwt_auth():
    db = StubDb()
    client = make_authed_client(db=db)
    token = make_jwt("user-jwt-1")

    resp = client.post(
        "/topics",
        json={"phrase": "macroeconomics"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201
    assert resp.json()["user_id"] == "user-jwt-1"


# ---------------------------------------------------------------------------
# Behavior 15: Invalid Bearer JWT -> 401
# ---------------------------------------------------------------------------

def test_invalid_bearer_jwt_returns_401():
    client = make_authed_client()

    resp = client.get("/topics", headers={"Authorization": "Bearer not-a-real-jwt"})

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Behavior 16: POST /digest/topics/:id/refresh — no recent refresh -> 200, card returned
# ---------------------------------------------------------------------------

def test_refresh_topic_card_success():
    from datetime import datetime, timezone, timedelta
    db = StubDb()
    # Seed a topic so the endpoint can look up the phrase
    db.topics = [{"id": "topic-1", "user_id": "user-1", "phrase": "space exploration", "display_order": 0}]
    old_refresh = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    db.digest = {
        "topic_cards": [
            {
                "id": "card-1",
                "topic_id": "topic-1",
                "status": "ok",
                "last_refreshed_at": old_refresh,
            }
        ]
    }
    orchestrator = StubOrchestrator()
    client = make_client(db=db, orchestrator=orchestrator)

    resp = client.post(
        "/digest/topics/topic-1/refresh",
        headers={"X-User-Id": "user-1"},
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert orchestrator.called_refresh_with == ("topic-1", "space exploration")


# ---------------------------------------------------------------------------
# Behavior 17: POST /digest/topics/:id/refresh — refreshed < 60 min ago -> 429
# ---------------------------------------------------------------------------

def test_refresh_topic_card_rate_limited():
    from datetime import datetime, timezone, timedelta
    db = StubDb()
    # Card refreshed only 5 minutes ago
    recent_refresh = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    db.digest = {
        "topic_cards": [
            {
                "id": "card-1",
                "topic_id": "topic-1",
                "status": "ok",
                "last_refreshed_at": recent_refresh,
            }
        ]
    }
    client = make_client(db=db)

    resp = client.post(
        "/digest/topics/topic-1/refresh",
        headers={"X-User-Id": "user-1"},
    )

    assert resp.status_code == 429
    body = resp.json()
    assert "retry_after" in body["detail"]
    assert "Refresh available at" in body["detail"]["detail"]
