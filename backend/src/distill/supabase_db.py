"""Supabase-backed implementation of the db interface expected by the API routes."""
from __future__ import annotations


class SupabaseDb:
    def __init__(self, client):
        self._db = client

    # ------------------------------------------------------------------
    # Topics
    # ------------------------------------------------------------------

    def get_topics(self, user_id: str) -> list[dict]:
        result = (
            self._db.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .order("display_order")
            .execute()
        )
        return result.data or []

    def count_topics(self, user_id: str) -> int:
        return len(self.get_topics(user_id))

    def create_topic(self, user_id: str, phrase: str) -> dict:
        count = self.count_topics(user_id)
        result = (
            self._db.table("topics")
            .insert({"user_id": user_id, "phrase": phrase, "display_order": count})
            .execute()
        )
        return result.data[0]

    def get_topic(self, topic_id: str) -> dict | None:
        result = (
            self._db.table("topics")
            .select("*")
            .eq("id", topic_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def update_topic(self, topic_id: str, data: dict) -> dict:
        result = (
            self._db.table("topics")
            .update(data)
            .eq("id", topic_id)
            .execute()
        )
        return result.data[0]

    def delete_topic(self, topic_id: str) -> None:
        self._db.table("topics").delete().eq("id", topic_id).execute()

    # ------------------------------------------------------------------
    # Digest + Topic Cards
    # ------------------------------------------------------------------

    def get_digest(self, user_id: str) -> dict | None:
        result = (
            self._db.table("digests")
            .select("*, topic_cards(*)")
            .eq("user_id", user_id)
            .order("generated_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def save_digest(self, user_id: str, digest: dict) -> dict:
        # One digest per user — delete any existing one (topic_cards cascade)
        self._db.table("digests").delete().eq("user_id", user_id).execute()
        row = self._db.table("digests").insert({"user_id": user_id}).execute().data[0]
        cards = digest.get("topic_cards", [])
        if cards:
            for card in cards:
                card["digest_id"] = row["id"]
            self._db.table("topic_cards").insert(cards).execute()
        return {**row, "topic_cards": cards}

    def update_topic_card(self, card_id: str, data: dict) -> dict:
        result = (
            self._db.table("topic_cards")
            .update(data)
            .eq("id", card_id)
            .execute()
        )
        return result.data[0]

    def get_topic_card(self, user_id: str, topic_id: str) -> dict | None:
        digest = self.get_digest(user_id)
        if not digest:
            return None
        return next(
            (c for c in digest.get("topic_cards", []) if c.get("topic_id") == topic_id),
            None,
        )

    # ------------------------------------------------------------------
    # Trending (global, world-readable)
    # ------------------------------------------------------------------

    def get_trending_topics(self) -> list[dict]:
        result = (
            self._db.table("trending_topics")
            .select("id, phrase, rank")
            .eq("active", True)
            .order("rank")
            .execute()
        )
        return result.data or []

    def get_trending_cards(self) -> list[dict]:
        result = (
            self._db.table("trending_topics")
            .select("id, phrase, rank, trending_cards(*)")
            .eq("active", True)
            .order("rank")
            .execute()
        )
        cards = []
        for topic in result.data or []:
            joined = topic.get("trending_cards")
            card = joined[0] if isinstance(joined, list) else joined
            card = card or {}
            cards.append(
                {
                    "trending_topic_id": topic["id"],
                    "phrase": topic["phrase"],
                    "status": card.get("status", "error"),
                    "tldr": card.get("tldr"),
                    "bullets": card.get("bullets"),
                    "sources": card.get("sources"),
                    "generated_at": card.get("generated_at"),
                }
            )
        return cards

    def save_trending_cards(self, cards) -> None:
        for card in cards:
            topic_id = card["trending_topic_id"]
            self._db.table("trending_cards").delete().eq(
                "trending_topic_id", topic_id
            ).execute()
            self._db.table("trending_cards").insert(card).execute()

    # ------------------------------------------------------------------
    # Settings (users table)
    # ------------------------------------------------------------------

    def get_settings(self, user_id: str) -> dict:
        result = (
            self._db.table("users")
            .select("delivery_time, device_token, timezone")
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else {}

    def update_settings(self, user_id: str, data: dict) -> dict:
        result = (
            self._db.table("users")
            .update(data)
            .eq("id", user_id)
            .execute()
        )
        return result.data[0] if result.data else data
