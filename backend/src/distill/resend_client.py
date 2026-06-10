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
