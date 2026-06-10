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
        sections = [self._render_card(c) for c in digest.topic_cards]
        button = (
            f'<p><a href="{self._app_base_url}" '
            f'style="display:inline-block;padding:10px 16px;background:#111;'
            f'color:#fff;text-decoration:none;border-radius:6px">'
            f"Open in Distill</a></p>"
        )
        return (
            '<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;'
            'max-width:600px;margin:0 auto;color:#111">'
            f"{''.join(sections)}{button}</div>"
        )

    def _render_card(self, result) -> str:
        if result.status != "ok" or result.card is None:
            return (
                '<section style="margin:24px 0;padding:16px;border:1px solid #eee;'
                'border-radius:8px">'
                "<p><em>This Topic Card couldn’t be generated. "
                "Open Distill to retry.</em></p></section>"
            )
        card = result.card
        bullets = "".join(f"<li>{b}</li>" for b in card.bullets)
        sources = "".join(
            f'<li><a href="{s.url}">{s.title}</a></li>' for s in card.sources
        )
        return (
            '<section style="margin:24px 0;padding:16px;border:1px solid #eee;'
            'border-radius:8px">'
            f'<h2 style="font-size:18px;margin:0 0 12px">{card.tldr}</h2>'
            f"<ul>{bullets}</ul>"
            '<p style="color:#666;font-size:13px;margin:12px 0 4px">Sources:</p>'
            f"<ul>{sources}</ul>"
            "</section>"
        )
