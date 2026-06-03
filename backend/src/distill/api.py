"""Distill API — FastAPI application."""
from __future__ import annotations

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
    """Validates Supabase JWTs (Bearer) or falls back to X-User-Id for tests."""

    def __init__(self, app, jwt_secret: str = ""):
        super().__init__(app)
        self._jwt_secret = jwt_secret

    async def dispatch(self, request: Request, call_next):
        user_id = self._extract_user_id(request)
        if not user_id:
            return Response(
                content='{"detail":"Unauthorized"}',
                status_code=401,
                media_type="application/json",
            )
        request.state.user_id = user_id
        return await call_next(request)

    def _extract_user_id(self, request: Request) -> str | None:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return self._decode_jwt(auth[7:])
        return request.headers.get("x-user-id") or None

    def _decode_jwt(self, token: str) -> str | None:
        if not self._jwt_secret:
            return None
        try:
            import jwt
            payload = jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
            return payload.get("sub")
        except Exception:
            return None


def create_app(db, orchestrator, jwt_secret: str = "") -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware, jwt_secret=jwt_secret)
    app.state.db = db
    app.state.orchestrator = orchestrator

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
        return request.app.state.db.get_digest(request.state.user_id)

    @app.post("/digest/generate")
    def generate_digest(request: Request):
        return request.app.state.orchestrator.generate(request.state.user_id)

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
        return request.app.state.orchestrator.refresh_card(user_id, topic_id)

    @app.patch("/settings")
    async def patch_settings(request: Request):
        body = await request.json()
        return request.app.state.db.update_settings(request.state.user_id, body)

    return app
