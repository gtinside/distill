from unittest.mock import MagicMock
from distill.resend_client import ResendClient


def test_send_posts_to_resend_with_auth_and_payload():
    http = MagicMock()
    http.post.return_value = MagicMock(status_code=200, json=lambda: {"id": "email-1"})
    client = ResendClient(
        api_key="re_test", from_email="digest@distill.app", http_client=http
    )

    result = client.send(
        to="maya@example.com", subject="Your Distill digest", html="<p>hi</p>"
    )

    assert result == {"id": "email-1"}
    http.post.assert_called_once_with(
        "https://api.resend.com/emails",
        headers={"Authorization": "Bearer re_test"},
        json={
            "from": "digest@distill.app",
            "to": ["maya@example.com"],
            "subject": "Your Distill digest",
            "html": "<p>hi</p>",
        },
    )
