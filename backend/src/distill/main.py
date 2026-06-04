"""Railway entry point — starts the scheduler loop."""
import os
import time

import uvicorn

from distill.api import create_app
from distill.db import get_client
from distill.digest_orchestrator import DigestOrchestrator
from distill.firebase_client import FirebaseFCMClient
from distill.push_notification_service import PushNotificationService
from distill.scheduler_worker import SchedulerWorker
from distill.synthesis_engine import SynthesisEngine


def _build_scheduler(supabase) -> SchedulerWorker:
    synthesis = SynthesisEngine(
        exa_client=_exa_client(),
        claude_client=_claude_client(),
    )
    orchestrator = DigestOrchestrator(synthesis_engine=synthesis)
    push_service = PushNotificationService(fcm_client=FirebaseFCMClient())

    def fetch_due_users():
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%H:%M")
        result = supabase.table("users").select("id").eq("delivery_time", now).execute()
        return [row["id"] for row in (result.data or [])]

    def persist_digest(user_id: str, digest: dict):
        supabase.table("digests").insert({"user_id": user_id}).execute()

    return SchedulerWorker(
        fetch_due_users=fetch_due_users,
        orchestrator=orchestrator,
        persist_digest=persist_digest,
        push_service=push_service,
    )


def _exa_client():
    from exa_py import Exa
    return Exa(os.environ["EXA_API_KEY"])


def _claude_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def main():
    supabase = get_client()
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", "")

    # Stub db/orchestrator for the API layer (real DB client to follow in a later slice)
    from distill.digest_orchestrator import DigestOrchestrator
    from distill.synthesis_engine import SynthesisEngine

    api_app = create_app(
        db=supabase,
        orchestrator=DigestOrchestrator(SynthesisEngine(_exa_client(), _claude_client())),
        jwt_secret=jwt_secret,
    )

    scheduler = _build_scheduler(supabase)

    import threading

    def scheduler_loop():
        while True:
            try:
                scheduler.tick()
            except Exception as e:
                print(f"[scheduler] error: {e}")
            time.sleep(60)

    threading.Thread(target=scheduler_loop, daemon=True).start()

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(api_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
