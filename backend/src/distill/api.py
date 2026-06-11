"""Distill API — FastAPI application."""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class TopicCreate(BaseModel):
    phrase: str


class TopicUpdate(BaseModel):
    phrase: str | None = None
    display_order: int | None = None


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates Supabase JWTs via local decode (tests) or Supabase Auth API (production)."""

    def __init__(self, app, jwt_secret: str = ""):
        super().__init__(app)
        self._jwt_secret = jwt_secret
        self._supabase_url = os.environ.get("SUPABASE_URL", "")
        self._anon_key = os.environ.get("SUPABASE_ANON_KEY", os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""))

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/trending"):
            return await call_next(request)
        user_id = await self._extract_user_id(request)
        if not user_id:
            return Response(
                content='{"detail":"Unauthorized"}',
                status_code=401,
                media_type="application/json",
            )
        request.state.user_id = user_id
        return await call_next(request)

    async def _extract_user_id(self, request: Request) -> str | None:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            # Try local JWT validation first (fast, works for test tokens)
            user_id = self._decode_jwt_local(token)
            if user_id:
                return user_id
            # Fall back to Supabase Auth API (works for real Apple-signed sessions)
            return await self._validate_via_supabase(token)
        return request.headers.get("x-user-id") or None

    def _decode_jwt_local(self, token: str) -> str | None:
        if not self._jwt_secret:
            return None
        try:
            import jwt
            payload = jwt.decode(
                token, self._jwt_secret, algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload.get("sub")
        except Exception:
            return None

    async def _validate_via_supabase(self, token: str) -> str | None:
        if not self._supabase_url:
            return None
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._supabase_url}/auth/v1/user",
                    headers={"Authorization": f"Bearer {token}", "apikey": self._anon_key},
                    timeout=5.0,
                )
            if resp.status_code == 200:
                return resp.json().get("id")
        except Exception:
            pass
        return None


def create_app(db, orchestrator, jwt_secret: str = "") -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware, jwt_secret=jwt_secret)
    app.state.db = db
    app.state.orchestrator = orchestrator

    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}

    @app.get("/trending")
    def get_trending(request: Request):
        cards = request.app.state.db.get_trending_cards()
        generated_at = next(
            (c["generated_at"] for c in cards if c.get("generated_at")), None
        )
        return {"generated_at": generated_at, "cards": cards}

    @app.post("/topics", status_code=201)
    def create_topic(body: TopicCreate, request: Request):
        user_id = request.state.user_id
        phrase = body.phrase

        if len(phrase) < 3 or len(phrase) > 60:
            raise HTTPException(status_code=422, detail="phrase must be 3-60 characters")
        if request.app.state.db.count_topics(user_id) >= 10:
            raise HTTPException(status_code=422, detail="user already has 10 topics")

        return request.app.state.db.create_topic(user_id, phrase)

    @app.get("/topics")
    def list_topics(request: Request):
        return request.app.state.db.get_topics(request.state.user_id)

    @app.patch("/topics/{topic_id}")
    async def update_topic(topic_id: str, body: TopicUpdate, request: Request):
        user_id = request.state.user_id
        topic = request.app.state.db.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        if topic["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        return request.app.state.db.update_topic(topic_id, body.model_dump(exclude_none=True))

    @app.delete("/topics/{topic_id}", status_code=204)
    def delete_topic(topic_id: str, request: Request):
        user_id = request.state.user_id
        topic = request.app.state.db.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        if topic["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        request.app.state.db.delete_topic(topic_id)

    @app.get("/digest")
    def get_digest(request: Request):
        result = request.app.state.db.get_digest(request.state.user_id)
        if result is None:
            raise HTTPException(status_code=404, detail="No digest found")
        return result

    @app.post("/digest/generate")
    def generate_digest(request: Request):
        user_id = request.state.user_id
        result = request.app.state.orchestrator.generate(user_id)
        cards = []
        for cr in result.topic_cards:
            card: dict = {"topic_id": cr.topic_id, "status": cr.status}
            if cr.card:
                card["tldr"] = cr.card.tldr
                card["bullets"] = cr.card.bullets
                card["sources"] = [{"title": s.title, "url": s.url} for s in cr.card.sources]
            cards.append(card)
        return request.app.state.db.save_digest(user_id, {"topic_cards": cards})

    @app.post("/digest/topics/{topic_id}/refresh")
    def refresh_topic_card(topic_id: str, request: Request):
        user_id = request.state.user_id
        card = request.app.state.db.get_topic_card(user_id, topic_id)
        if card:
            last_refreshed_at = card.get("last_refreshed_at")
            if last_refreshed_at:
                last_refreshed = datetime.fromisoformat(last_refreshed_at)
                if last_refreshed.tzinfo is None:
                    last_refreshed = last_refreshed.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                elapsed = now - last_refreshed
                if elapsed < timedelta(minutes=60):
                    retry_after = last_refreshed + timedelta(minutes=60)
                    retry_time_str = retry_after.strftime("%H:%M")
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "detail": f"Refresh available at {retry_time_str}",
                            "retry_after": retry_after.isoformat(),
                        },
                    )
        topic = request.app.state.db.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        cr = request.app.state.orchestrator.refresh_card(topic_id, topic["phrase"])
        now_iso = datetime.now(timezone.utc).isoformat()
        card_data: dict = {"status": cr.status, "last_refreshed_at": now_iso}
        if cr.card:
            card_data["tldr"] = cr.card.tldr
            card_data["bullets"] = cr.card.bullets
            card_data["sources"] = [{"title": s.title, "url": s.url} for s in cr.card.sources]
        if not card:
            raise HTTPException(status_code=404, detail="No existing card — generate a digest first")
        return request.app.state.db.update_topic_card(card["id"], card_data)

    @app.get("/settings")
    def get_settings(request: Request):
        return request.app.state.db.get_settings(request.state.user_id)

    @app.patch("/settings")
    async def patch_settings(request: Request):
        body = await request.json()
        return request.app.state.db.update_settings(request.state.user_id, body)

    return app
