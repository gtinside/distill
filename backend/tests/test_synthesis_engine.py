import pytest
from distill.synthesis_engine import ExaResult, SynthesisEngine, SynthesisError


def make_exa_results():
    return [
        ExaResult(
            title="Fed holds rates steady amid inflation concerns",
            url="https://example.com/fed-rates",
            text="The Federal Reserve held interest rates steady on Wednesday, citing persistent inflation. Officials signaled they expect to cut rates later this year if inflation continues to fall.",
        ),
        ExaResult(
            title="Fed minutes reveal divided committee on rate path",
            url="https://example.com/fed-minutes",
            text="Minutes from the last Fed meeting show committee members are split on how quickly to cut rates. Some members want to wait for more data before acting.",
        ),
    ]


VALID_RESPONSE = """{
    "tldr": "The Fed held rates steady, signalling cuts may come later this year.",
    "bullets": [
        "Fed kept rates unchanged amid persistent inflation",
        "Officials expect cuts later this year if inflation falls",
        "Committee is divided on the pace of rate reductions",
        "Markets reacted with mild optimism to the announcement"
    ],
    "sources": [
        {"title": "Fed holds rates steady amid inflation concerns", "url": "https://example.com/fed-rates"},
        {"title": "Fed minutes reveal divided committee on rate path", "url": "https://example.com/fed-minutes"}
    ]
}"""


def make_stub_claude(response_json: str, call_count: dict | None = None):
    """Returns a minimal Claude client stub that always returns the given response text."""

    class FakeMessage:
        content = [type("Block", (), {"text": response_json})()]

    class FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                if call_count is not None:
                    call_count["n"] += 1
                return FakeMessage()

    return FakeClient()


def test_malformed_claude_response_retries_then_raises():
    call_count = {"n": 0}
    engine = SynthesisEngine(claude_client=make_stub_claude("not valid json {", call_count))

    with pytest.raises(SynthesisError):
        engine.synthesize(topic="Fed policy", exa_results=make_exa_results())

    assert call_count["n"] == 3


def test_empty_results_raises_synthesis_error():
    engine = SynthesisEngine(claude_client=make_stub_claude(VALID_RESPONSE))
    with pytest.raises(SynthesisError):
        engine.synthesize(topic="Fed policy", exa_results=[])


def test_valid_results_returns_topic_card():
    engine = SynthesisEngine(claude_client=make_stub_claude(VALID_RESPONSE))
    card = engine.synthesize(topic="Fed policy", exa_results=make_exa_results())

    assert card.tldr
    assert 4 <= len(card.bullets) <= 5
    assert len(card.sources) >= 1
    assert all(s.url for s in card.sources)
