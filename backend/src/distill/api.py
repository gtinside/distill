"""Distill API — FastAPI application."""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
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
        # Trusting an X-User-Id header is a test-only convenience and a full auth
        # bypass if ever enabled in production. Off unless ALLOW_HEADER_AUTH=1.
        self._allow_header_auth = os.environ.get("ALLOW_HEADER_AUTH") == "1"

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
            # Fall back to Supabase Auth API (works for real Supabase sessions)
            return await self._validate_via_supabase(token)
        if self._allow_header_auth:
            return request.headers.get("x-user-id") or None
        return None

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


def _run_digest_generation(orchestrator, db, user_id: str) -> None:
    """Generate a User's Digest and persist it. Runs in a background task."""
    result = orchestrator.generate(user_id)
    cards = []
    for cr in result.topic_cards:
        card: dict = {"topic_id": cr.topic_id, "status": cr.status}
        if cr.card:
            card["tldr"] = cr.card.tldr
            card["bullets"] = cr.card.bullets
            card["sources"] = [{"title": s.title, "url": s.url} for s in cr.card.sources]
        cards.append(card)
    db.save_digest(user_id, {"topic_cards": cards})


def create_app(db, orchestrator, jwt_secret: str = "") -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware, jwt_secret=jwt_secret)
    app.state.db = db
    app.state.orchestrator = orchestrator
    app.state.generate_cooldowns = {}

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

    @app.post("/digest/generate", status_code=202)
    def generate_digest(request: Request, background_tasks: BackgroundTasks):
        # Synthesis fans out several slow Claude/Exa calls — too long for the
        # web tier to wait on synchronously. Run it in the background and return
        # immediately; the client polls GET /digest for the result.
        user_id = request.state.user_id
        # Per-user cooldown so generation can't be spammed (DoS / Claude bill).
        import time
        cooldowns = request.app.state.generate_cooldowns
        now = time.monotonic()
        if now - cooldowns.get(user_id, 0.0) < 300:
            raise HTTPException(
                status_code=429,
                detail="A Digest was just generated — try again in a few minutes.",
            )
        cooldowns[user_id] = now
        background_tasks.add_task(
            _run_digest_generation,
            request.app.state.orchestrator,
            request.app.state.db,
            user_id,
        )
        return {"status": "generating"}

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
        # Whitelist updatable fields — never let the client set arbitrary
        # columns (email, id, apple_sub, ...).
        allowed = {"delivery_time", "timezone"}
        data = {k: v for k, v in body.items() if k in allowed}
        return request.app.state.db.update_settings(request.state.user_id, data)

    return app
