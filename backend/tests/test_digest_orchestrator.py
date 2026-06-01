import pytest
from distill.synthesis_engine import ExaResult, SynthesisEngine, SynthesisError
from distill.digest_orchestrator import Digest, DigestOrchestrator
from tests.test_synthesis_engine import make_stub_claude, VALID_RESPONSE


def make_fetch_topics(*phrases: str):
    """Stub that returns a fixed list of (topic_id, phrase) tuples."""
    topics = [(f"topic-{i}", phrase) for i, phrase in enumerate(phrases)]
    return lambda user_id: topics


def make_fetch_sources():
    """Stub that returns two fixture ExaResults for any topic phrase."""
    results = [
        ExaResult(title="Article A", url="https://example.com/a", text="Content A"),
        ExaResult(title="Article B", url="https://example.com/b", text="Content B"),
    ]
    return lambda phrase: results


def make_engine(response_json=VALID_RESPONSE):
    return SynthesisEngine(claude_client=make_stub_claude(response_json))


# --- Behavior 2: zero Topics ---

def test_zero_topics_returns_empty_digest():
    orchestrator = DigestOrchestrator(
        fetch_topics=make_fetch_topics(),
        fetch_sources=make_fetch_sources(),
        synthesis_engine=make_engine(),
    )
    digest = orchestrator.generate(user_id="user-1")

    assert digest.topic_cards == []


# --- Behavior 3: one Topic fails, rest succeed ---

def make_engine_fails_for(failing_phrase: str):
    """SynthesisEngine stub that raises SynthesisError for one specific topic phrase."""
    real_engine = make_engine()

    class MixedEngine:
        def synthesize(self, topic: str, exa_results):
            if topic == failing_phrase:
                raise SynthesisError("Simulated failure")
            return real_engine.synthesize(topic, exa_results)

    return MixedEngine()


def test_partial_failure_produces_mixed_digest():
    orchestrator = DigestOrchestrator(
        fetch_topics=make_fetch_topics("Fed policy", "Space exploration", "Watch releases"),
        fetch_sources=make_fetch_sources(),
        synthesis_engine=make_engine_fails_for("Space exploration"),
    )
    digest = orchestrator.generate(user_id="user-1")

    assert len(digest.topic_cards) == 3
    statuses = {r.topic_id: r.status for r in digest.topic_cards}
    assert statuses["topic-0"] == "ok"
    assert statuses["topic-1"] == "error"
    assert statuses["topic-2"] == "ok"


# --- Behavior 4: all Topics fail ---

def make_engine_always_fails():
    class AlwaysFailEngine:
        def synthesize(self, topic: str, exa_results):
            raise SynthesisError("Always fails")

    return AlwaysFailEngine()


def test_all_topics_fail_returns_all_error_cards():
    orchestrator = DigestOrchestrator(
        fetch_topics=make_fetch_topics("Fed policy", "Space exploration"),
        fetch_sources=make_fetch_sources(),
        synthesis_engine=make_engine_always_fails(),
    )
    digest = orchestrator.generate(user_id="user-1")

    assert len(digest.topic_cards) == 2
    assert all(r.status == "error" for r in digest.topic_cards)
    assert all(r.card is None for r in digest.topic_cards)


# --- Behavior 1: all Topics succeed ---

def test_all_topics_succeed_returns_ok_cards():
    orchestrator = DigestOrchestrator(
        fetch_topics=make_fetch_topics("Fed policy", "Space exploration"),
        fetch_sources=make_fetch_sources(),
        synthesis_engine=make_engine(),
    )
    digest = orchestrator.generate(user_id="user-1")

    assert len(digest.topic_cards) == 2
    assert all(r.status == "ok" for r in digest.topic_cards)
    assert all(r.card is not None for r in digest.topic_cards)
