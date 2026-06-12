"""Trending feature tests — SupabaseDb shaping + public GET /trending."""
from unittest.mock import MagicMock

from starlette.testclient import TestClient

from distill.supabase_db import SupabaseDb


# ---------------------------------------------------------------------------
# SupabaseDb.get_trending_cards — shape, joined to trending topic phrase
# ---------------------------------------------------------------------------

def _chain_returning(rows):
    """Build a Supabase query-builder mock whose execute() returns rows."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.order.return_value = chain
    chain.execute.return_value = MagicMock(data=rows)
    return chain


def test_get_trending_cards_shape():
    rows = [
        {
            "id": "tt-1",
            "phrase": "EU AI regulation",
            "rank": 0,
            "trending_cards": [
                {
                    "status": "ok",
                    "tldr": "Brussels moves on AI.",
                    "bullets": ["a", "b"],
                    "sources": [{"title": "T", "url": "https://e.com"}],
                    "generated_at": "2026-06-11T05:00:00+00:00",
                }
            ],
        },
        {
            "id": "tt-2",
            "phrase": "Fed policy",
            "rank": 1,
            "trending_cards": [{"status": "error", "generated_at": "2026-06-11T05:00:00+00:00"}],
        },
    ]
    chain = _chain_returning(rows)
    client = MagicMock()
    client.table.return_value = chain

    cards = SupabaseDb(client).get_trending_cards()

    assert cards[0] == {
        "trending_topic_id": "tt-1",
        "phrase": "EU AI regulation",
        "status": "ok",
        "tldr": "Brussels moves on AI.",
        "bullets": ["a", "b"],
        "sources": [{"title": "T", "url": "https://e.com"}],
        "generated_at": "2026-06-11T05:00:00+00:00",
    }
    assert cards[1]["trending_topic_id"] == "tt-2"
    assert cards[1]["status"] == "error"
    assert cards[1]["tldr"] is None


def test_get_trending_topics_orders_by_rank_and_filters_active():
    chain = _chain_returning([{"id": "tt-1", "phrase": "Fed policy", "rank": 0}])
    client = MagicMock()
    client.table.return_value = chain

    topics = SupabaseDb(client).get_trending_topics()

    chain.eq.assert_called_once_with("active", True)
    chain.order.assert_called_once_with("rank")
    assert topics[0]["phrase"] == "Fed policy"


# ---------------------------------------------------------------------------
# GET /trending — public (no auth), returns the db's trending cards
# ---------------------------------------------------------------------------

class StubTrendingDb:
    def __init__(self, cards):
        self._cards = cards

    def get_trending_cards(self):
        return self._cards


class StubOrchestrator:
    def generate(self, user_id):  # pragma: no cover - unused here
        from distill.digest_orchestrator import Digest
        return Digest()


def _make_trending_client(cards):
    from distill.api import create_app
    app = create_app(db=StubTrendingDb(cards), orchestrator=StubOrchestrator())
    return TestClient(app, raise_server_exceptions=True)


def test_get_trending_public_no_auth_header():
    cards = [
        {
            "trending_topic_id": "tt-1",
            "phrase": "EU AI regulation",
            "status": "ok",
            "tldr": "Brussels moves on AI.",
            "bullets": ["a", "b"],
            "sources": [{"title": "T", "url": "https://e.com"}],
            "generated_at": "2026-06-11T05:00:00+00:00",
        }
    ]
    client = _make_trending_client(cards)

    resp = client.get("/trending")  # no Authorization header

    assert resp.status_code == 200
    body = resp.json()
    assert body["generated_at"] == "2026-06-11T05:00:00+00:00"
    assert body["cards"][0]["trending_topic_id"] == "tt-1"
    assert body["cards"][0]["phrase"] == "EU AI regulation"


def test_get_trending_generated_at_null_when_no_cards():
    client = _make_trending_client([])

    resp = client.get("/trending")

    assert resp.status_code == 200
    assert resp.json() == {"generated_at": None, "cards": []}


def test_trending_is_in_public_allowlist_but_other_paths_still_401():
    client = _make_trending_client([])

    # /trending is public
    assert client.get("/trending").status_code == 200
    # a protected path still requires auth
    assert client.get("/topics").status_code == 401
