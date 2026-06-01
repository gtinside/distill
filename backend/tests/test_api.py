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

    # Settings ----------------------------------------------------------------

    def get_settings(self, user_id: str) -> dict:
        return self.settings

    def update_settings(self, user_id: str, data: dict) -> dict:
        self.settings.update(data)
        return self.settings


class StubOrchestrator:
    """In-memory stub for DigestOrchestrator."""

    def __init__(self, result=None):
        self.called_with: str | None = None
        self._result = result or {"topic_cards": []}

    def generate(self, user_id: str):
        self.called_with = user_id
        return self._result


# ---------------------------------------------------------------------------
# Client factory — used by every test
# ---------------------------------------------------------------------------

def make_client(db=None, orchestrator=None) -> TestClient:
    from distill.api import create_app
    app = create_app(db=db or StubDb(), orchestrator=orchestrator or StubOrchestrator())
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
    orchestrator = StubOrchestrator(result={"topic_cards": [{"topic_id": "t42", "status": "ok"}]})
    client = make_client(orchestrator=orchestrator)

    resp = client.post("/digest/generate", headers={"X-User-Id": "user-99"})

    assert resp.status_code == 200
    assert resp.json()["topic_cards"][0]["topic_id"] == "t42"
    assert orchestrator.called_with == "user-99"


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
# Behavior 10: Any endpoint without X-User-Id header -> 401
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
