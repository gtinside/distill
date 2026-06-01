from unittest.mock import MagicMock
from distill.push_notification_service import PushNotificationService


def make_fcm_client():
    return MagicMock()


# --- Behavior 1: single topic ---

def test_single_topic_sends_correct_body():
    fcm = make_fcm_client()
    service = PushNotificationService(fcm_client=fcm)

    service.send(device_token="tok-abc", topic_phrases=["Fed policy"])

    fcm.send.assert_called_once_with(
        token="tok-abc",
        title="Distill",
        body="Your digest is ready — Fed policy",
    )


# --- Behavior 2: two topics ---

def test_two_topics_sends_correct_body():
    fcm = make_fcm_client()
    service = PushNotificationService(fcm_client=fcm)

    service.send(device_token="tok-abc", topic_phrases=["Fed policy", "Space exploration"])

    fcm.send.assert_called_once_with(
        token="tok-abc",
        title="Distill",
        body="Your digest is ready — Fed policy, Space exploration",
    )


# --- Behavior 3: three or more topics ---

def test_three_topics_sends_plus_n_more_body():
    fcm = make_fcm_client()
    service = PushNotificationService(fcm_client=fcm)

    service.send(
        device_token="tok-abc",
        topic_phrases=["Fed policy", "Space exploration", "Watch releases"],
    )

    fcm.send.assert_called_once_with(
        token="tok-abc",
        title="Distill",
        body="Your digest is ready — Fed policy, Space exploration +1 more",
    )


def test_five_topics_sends_plus_n_more_body():
    fcm = make_fcm_client()
    service = PushNotificationService(fcm_client=fcm)

    service.send(
        device_token="tok-abc",
        topic_phrases=["Fed policy", "Space exploration", "A", "B", "C"],
    )

    fcm.send.assert_called_once_with(
        token="tok-abc",
        title="Distill",
        body="Your digest is ready — Fed policy, Space exploration +3 more",
    )


# --- Behavior 4: no device token ---

def test_none_device_token_does_not_call_fcm():
    fcm = make_fcm_client()
    service = PushNotificationService(fcm_client=fcm)

    service.send(device_token=None, topic_phrases=["Fed policy"])

    fcm.send.assert_not_called()


def test_empty_device_token_does_not_call_fcm():
    fcm = make_fcm_client()
    service = PushNotificationService(fcm_client=fcm)

    service.send(device_token="", topic_phrases=["Fed policy"])

    fcm.send.assert_not_called()


# --- Behavior 5: zero topics ---

def test_zero_topics_sends_bare_ready_body():
    fcm = make_fcm_client()
    service = PushNotificationService(fcm_client=fcm)

    service.send(device_token="tok-abc", topic_phrases=[])

    fcm.send.assert_called_once_with(
        token="tok-abc",
        title="Distill",
        body="Your digest is ready",
    )
