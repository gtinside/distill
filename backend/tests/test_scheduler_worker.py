from distill.scheduler_worker import SchedulerWorker
from distill.digest_orchestrator import Digest


# --- Helpers ---

def make_worker(
    due_users=None,
    generate_fn=None,
    persist_calls=None,
    push_calls=None,
):
    """Build a SchedulerWorker with controllable stubs."""

    def fetch_due_users():
        return due_users if due_users is not None else []

    class StubOrchestrator:
        def generate(self, user_id):
            if generate_fn is not None:
                return generate_fn(user_id)
            return Digest()

    class StubEmailService:
        def send(self, user_id, digest):
            if push_calls is not None:
                push_calls.append((user_id, digest))

    _persist_calls = persist_calls if persist_calls is not None else []

    def persist_digest(user_id, digest):
        _persist_calls.append((user_id, digest))

    return SchedulerWorker(
        fetch_due_users=fetch_due_users,
        orchestrator=StubOrchestrator(),
        persist_digest=persist_digest,
        email_service=StubEmailService(),
    ), _persist_calls


# --- Behavior 1: no due users — nothing else is called ---

def test_no_due_users_calls_nothing():
    persist_calls = []
    push_calls = []
    worker, _ = make_worker(
        due_users=[],
        persist_calls=persist_calls,
        push_calls=push_calls,
    )

    worker.tick()

    assert persist_calls == []
    assert push_calls == []


# --- Behavior 2: one due user, generation succeeds ---

def test_one_due_user_persists_and_pushes():
    fixed_digest = Digest()
    persist_calls = []
    push_calls = []

    worker, _ = make_worker(
        due_users=["user-1"],
        generate_fn=lambda user_id: fixed_digest,
        persist_calls=persist_calls,
        push_calls=push_calls,
    )

    worker.tick()

    assert persist_calls == [("user-1", fixed_digest)]
    assert push_calls == [("user-1", fixed_digest)]


# --- Behavior 3: two due users — both processed ---

def test_two_due_users_both_persisted():
    digests = {}
    persist_calls = []

    def generate_fn(user_id):
        d = Digest()
        digests[user_id] = d
        return d

    worker, _ = make_worker(
        due_users=["user-1", "user-2"],
        generate_fn=generate_fn,
        persist_calls=persist_calls,
    )

    worker.tick()

    assert len(persist_calls) == 2
    persisted_user_ids = [uid for uid, _ in persist_calls]
    assert "user-1" in persisted_user_ids
    assert "user-2" in persisted_user_ids


# --- Behavior 4: generation raises — worker continues to next user ---

def test_generation_failure_skips_user_and_continues():
    persist_calls = []

    def generate_fn(user_id):
        if user_id == "user-bad":
            raise RuntimeError("generation exploded")
        return Digest()

    worker, _ = make_worker(
        due_users=["user-bad", "user-ok"],
        generate_fn=generate_fn,
        persist_calls=persist_calls,
    )

    worker.tick()  # must not raise

    persisted_user_ids = [uid for uid, _ in persist_calls]
    assert "user-bad" not in persisted_user_ids
    assert "user-ok" in persisted_user_ids
