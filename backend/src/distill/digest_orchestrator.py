from dataclasses import dataclass, field
from distill.synthesis_engine import SynthesisEngine, SynthesisError, TopicCard


@dataclass
class TopicCardResult:
    topic_id: str
    card: TopicCard | None
    status: str  # "ok" | "error"


@dataclass
class Digest:
    topic_cards: list[TopicCardResult] = field(default_factory=list)


class DigestOrchestrator:
    _MAX_RETRIES = 3

    def __init__(self, fetch_topics, fetch_sources, synthesis_engine: SynthesisEngine):
        self._fetch_topics = fetch_topics
        self._fetch_sources = fetch_sources
        self._synthesis_engine = synthesis_engine

    def generate(self, user_id: str) -> Digest:
        topics = self._fetch_topics(user_id)
        return Digest(topic_cards=[self._generate_card(tid, phrase) for tid, phrase in topics])

    def refresh_card(self, topic_id: str, phrase: str) -> TopicCardResult:
        return self._generate_card(topic_id, phrase)

    def _generate_card(self, topic_id: str, phrase: str) -> TopicCardResult:
        for _ in range(self._MAX_RETRIES):
            try:
                exa_results = self._fetch_sources(phrase)
                card = self._synthesis_engine.synthesize(phrase, exa_results)
                return TopicCardResult(topic_id=topic_id, card=card, status="ok")
            except Exception:
                continue
        return TopicCardResult(topic_id=topic_id, card=None, status="error")
