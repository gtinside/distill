"""Distill API — FastAPI application."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class TopicCreate(BaseModel):
    phrase: str


# ---------------------------------------------------------------------------
# Middleware: enforce X-User-Id before route processing
# ---------------------------------------------------------------------------

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.headers.get("x-user-id"):
            return Response(
                content='{"detail":"Missing X-User-Id header"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# App factory (accepts injectable db and orchestrator stubs)
# ---------------------------------------------------------------------------

def create_app(db, orchestrator) -> FastAPI:
    app = FastAPI()

    # Auth middleware runs before route dispatch (and before body parsing)
    app.add_middleware(AuthMiddleware)

    # Store dependencies on app state so they're reachable inside routes
    app.state.db = db
    app.state.orchestrator = orchestrator

    # ------------------------------------------------------------------
    # Topics
    # ------------------------------------------------------------------

    @app.post("/topics", status_code=201)
    def create_topic(body: TopicCreate, request: Request):
        user_id = request.headers.get("x-user-id")
        phrase = body.phrase

        if len(phrase) < 3 or len(phrase) > 60:
            raise HTTPException(status_code=422, detail="phrase must be 3-60 characters")

        if request.app.state.db.count_topics(user_id) >= 10:
            raise HTTPException(status_code=422, detail="user already has 10 topics")

        topic = request.app.state.db.create_topic(user_id, phrase)
        return topic

    @app.get("/topics")
    def list_topics(request: Request):
        user_id = request.headers.get("x-user-id")
        return request.app.state.db.get_topics(user_id)

    @app.patch("/topics/{topic_id}")
    def update_topic(topic_id: str, request: Request):
        # body read via middleware-safe approach handled at call site
        pass

    @app.delete("/topics/{topic_id}", status_code=204)
    def delete_topic(topic_id: str, request: Request):
        request.app.state.db.delete_topic(topic_id)

    # ------------------------------------------------------------------
    # Digest
    # ------------------------------------------------------------------

    @app.get("/digest")
    def get_digest(request: Request):
        user_id = request.headers.get("x-user-id")
        return request.app.state.db.get_digest(user_id)

    @app.post("/digest/generate")
    def generate_digest(request: Request):
        user_id = request.headers.get("x-user-id")
        digest = request.app.state.orchestrator.generate(user_id)
        return digest

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    @app.patch("/settings")
    async def patch_settings(request: Request):
        user_id = request.headers.get("x-user-id")
        body = await request.json()
        return request.app.state.db.update_settings(user_id, body)

    return app
