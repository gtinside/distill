from unittest.mock import MagicMock
from distill.email_digest_service import EmailDigestService


def make_service(recipient):
    email_client = MagicMock()
    service = EmailDigestService(
        email_client=email_client,
        fetch_recipient=lambda user_id: recipient,
        app_base_url="https://distill.app",
    )
    return service, email_client


def _empty_digest():
    from distill.digest_orchestrator import Digest
    return Digest(topic_cards=[])


def _ok_digest():
    from distill.digest_orchestrator import Digest, TopicCardResult
    from distill.synthesis_engine import TopicCard, Source

    card = TopicCard(
        tldr="Rates held steady.",
        bullets=["No hike", "Dovish tone"],
        sources=[Source(title="Fed statement", url="https://fed.gov/x")],
    )
    return Digest(topic_cards=[TopicCardResult(topic_id="t1", card=card, status="ok")])


def _error_digest():
    from distill.digest_orchestrator import Digest, TopicCardResult
    return Digest(topic_cards=[TopicCardResult(topic_id="t1", card=None, status="error")])


# --- Subject formatting ---

def test_subject_single_topic():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )
    service.send("user-1", digest=_empty_digest())
    assert client.send.call_args.kwargs["subject"] == "Your Distill digest — Fed policy"


def test_subject_three_topics_truncates():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy", "Space", "Watches"]}
    )
    service.send("user-1", digest=_empty_digest())
    assert (
        client.send.call_args.kwargs["subject"]
        == "Your Distill digest — Fed policy, Space +1 more"
    )


# --- HTML body ---

def test_html_includes_tldr_bullets_and_source():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )
    service.send("user-1", digest=_ok_digest())
    html = client.send.call_args.kwargs["html"]
    assert "Rates held steady." in html
    assert "No hike" in html
    assert "Dovish tone" in html
    assert "https://fed.gov/x" in html


def test_html_includes_open_in_distill_link():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )
    service.send("user-1", digest=_ok_digest())
    html = client.send.call_args.kwargs["html"]
    assert "https://distill.app" in html
    assert "Open in Distill" in html


def test_html_renders_error_state_for_failed_card():
    service, client = make_service(
        {"email": "maya@example.com", "topic_phrases": ["Fed policy"]}
    )
    service.send("user-1", digest=_error_digest())
    html = client.send.call_args.kwargs["html"]
    assert "couldn’t be generated" in html


def test_no_email_does_not_send():
    service, client = make_service({"email": None, "topic_phrases": ["Fed policy"]})
    service.send("user-1", digest=_ok_digest())
    client.send.assert_not_called()
