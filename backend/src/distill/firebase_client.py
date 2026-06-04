import json
import os

import firebase_admin
from firebase_admin import credentials, messaging


class FirebaseFCMClient:
    def __init__(self):
        cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
        if cred_json and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(cred_json))
            firebase_admin.initialize_app(cred)

    def send(self, token: str, title: str, body: str) -> None:
        if not token or not firebase_admin._apps:
            return
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
        )
        messaging.send(message)
