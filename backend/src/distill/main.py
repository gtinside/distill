"""Railway entry point — starts the scheduler loop and API server."""
import logging
import os
import threading
import time

import uvicorn

from distill.api import create_app
from distill.db import get_client
from distill.firebase_client import FirebaseFCMClient
from distill.push_notification_service import PushNotificationService
from distill.scheduler_worker import SchedulerWorker
from distill.supabase_db import SupabaseDb

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _build_orchestrator(db):
    from distill.digest_orchestrator import DigestOrchestrator
    from distill.synthesis_engine import SynthesisEngine, ExaResult
    from exa_py import Exa
    import anthropic

    exa_client = Exa(os.environ["EXA_API_KEY"])
    synthesis = SynthesisEngine(
        claude_client=anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]),
    )

    def fetch_topics(user_id: str):
        topics = db.get_topics(user_id)
        return [(t["id"], t["phrase"]) for t in topics]

    def fetch_sources(phrase: str):
        results = exa_client.search_and_contents(phrase, num_results=5, text=True)
        return [ExaResult(title=r.title or "", url=r.url, text=r.text or "")
                for r in results.results]

    return DigestOrchestrator(
        fetch_topics=fetch_topics,
        fetch_sources=fetch_sources,
        synthesis_engine=synthesis,
    )


def _build_scheduler(supabase, orchestrator) -> SchedulerWorker:
    push_service = PushNotificationService(fcm_client=FirebaseFCMClient())

    def fetch_due_users():
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%H:%M")
        result = supabase.table("users").select("id, device_token").execute()
        return [row["id"] for row in (result.data or [])
                if row.get("delivery_time", "")[:5] == now]

    def persist_digest(user_id: str, digest: dict):
        from distill.supabase_db import SupabaseDb
        SupabaseDb(supabase).save_digest(user_id, digest)

    return SchedulerWorker(
        fetch_due_users=fetch_due_users,
        orchestrator=orchestrator,
        persist_digest=persist_digest,
        push_service=push_service,
    )


def scheduler_loop(supabase, orchestrator):
    # Delay scheduler start so API can pass healthcheck first
    time.sleep(10)
    try:
        worker = _build_scheduler(supabase, orchestrator)
    except Exception as e:
        log.error(f"[scheduler] failed to initialise: {e}")
        return
    while True:
        try:
            worker.tick()
        except Exception as e:
            log.error(f"[scheduler] tick error: {e}")
        time.sleep(60)


def main():
    supabase = get_client()
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", "")

    db = SupabaseDb(supabase)
    orchestrator = _build_orchestrator(db)
    api_app = create_app(db=db, orchestrator=orchestrator, jwt_secret=jwt_secret)

    threading.Thread(target=scheduler_loop, args=(supabase, orchestrator), daemon=True).start()

    port = int(os.environ.get("PORT", 8000))
    log.info(f"Starting API on port {port}")
    uvicorn.run(api_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
