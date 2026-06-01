class PushNotificationService:
    _TITLE = "Distill"

    def __init__(self, fcm_client):
        self._fcm_client = fcm_client

    def send(self, device_token: str, topic_phrases: list[str]) -> None:
        if not device_token:
            return
        self._fcm_client.send(
            token=device_token,
            title=self._TITLE,
            body=self._format_body(topic_phrases),
        )

    @staticmethod
    def _format_body(topic_phrases: list[str]) -> str:
        n = len(topic_phrases)
        if n == 0:
            return "Your digest is ready"
        if n == 1:
            return f"Your digest is ready — {topic_phrases[0]}"
        if n == 2:
            return f"Your digest is ready — {topic_phrases[0]}, {topic_phrases[1]}"
        remainder = n - 2
        return (
            f"Your digest is ready — {topic_phrases[0]}, {topic_phrases[1]}"
            f" +{remainder} more"
        )
