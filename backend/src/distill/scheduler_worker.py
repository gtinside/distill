class SchedulerWorker:
    def __init__(self, fetch_due_users, orchestrator, persist_digest, push_service):
        self._fetch_due_users = fetch_due_users
        self._orchestrator = orchestrator
        self._persist_digest = persist_digest
        self._push_service = push_service

    def tick(self):
        user_ids = self._fetch_due_users()
        for user_id in user_ids:
            try:
                digest = self._orchestrator.generate(user_id)
                self._persist_digest(user_id, digest)
                self._push_service.send(user_id, digest)
            except Exception:
                continue
