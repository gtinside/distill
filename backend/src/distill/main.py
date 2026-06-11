"""Railway entry point — starts the scheduler loop and API server."""
import logging
import os
import threading
import time

import uvicorn

from distill.api import create_app
from distill.db import get_client
from distill.email_digest_service import EmailDigestService
from distill.resend_client import ResendClient
from distill.scheduler_worker import SchedulerWorker
from distill.scheduling import user_is_due
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
    db = SupabaseDb(supabase)

    resend = ResendClient(
        api_key=os.environ["RESEND_API_KEY"],
        from_email=os.environ["RESEND_FROM_EMAIL"],
    )

    def fetch_recipient(user_id: str) -> dict:
        row = supabase.table("users").select("email").eq("id", user_id).execute()
        email = row.data[0]["email"] if row.data else None
        topic_phrases = [t["phrase"] for t in db.get_topics(user_id)]
        return {"email": email, "topic_phrases": topic_phrases}

    email_service = EmailDigestService(
        email_client=resend,
        fetch_recipient=fetch_recipient,
        app_base_url=os.environ.get("APP_BASE_URL", "https://distill.app"),
    )

    def fetch_due_users():
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        result = supabase.table("users").select("id, delivery_time, timezone").execute()
        return [
            row["id"]
            for row in (result.data or [])
            if user_is_due(now, row.get("delivery_time", ""), row.get("timezone", "UTC"))
        ]

    def persist_digest(user_id: str, digest):
        db.save_digest(user_id, digest)

    return SchedulerWorker(
        fetch_due_users=fetch_due_users,
        orchestrator=orchestrator,
        persist_digest=persist_digest,
        email_service=email_service,
    )


def generate_trending(db, orchestrator):
    """Build/refresh the global trending Digest: synthesize a card per active
    trending topic and upsert the results into trending_cards."""
    topics = db.get_trending_topics()
    digest = orchestrator.generate_cards([(t["id"], t["phrase"]) for t in topics])
    cards = []
    for cr in digest.topic_cards:
        card = {"trending_topic_id": cr.topic_id, "status": cr.status}
        if cr.card:
            card["tldr"] = cr.card.tldr
            card["bullets"] = cr.card.bullets
            card["sources"] = [{"title": s.title, "url": s.url} for s in cr.card.sources]
        cards.append(card)
    db.save_trending_cards(cards)
    return cards


def scheduler_loop(supabase, orchestrator):
    # Delay scheduler start so API can pass healthcheck first
    time.sleep(10)
    try:
        worker = _build_scheduler(supabase, orchestrator)
    except Exception as e:
        log.error(f"[scheduler] failed to initialise: {e}")
        return
    db = SupabaseDb(supabase)
    trending_refresh_utc = os.environ.get("TRENDING_REFRESH_UTC", "05:00")
    last_trending_date = None
    while True:
        try:
            worker.tick()
        except Exception as e:
            log.error(f"[scheduler] tick error: {e}")
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if (
                now.strftime("%H:%M") >= trending_refresh_utc
                and last_trending_date != now.date()
            ):
                generate_trending(db, orchestrator)
                last_trending_date = now.date()
        except Exception as e:
            log.error(f"[scheduler] trending refresh error: {e}")
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
