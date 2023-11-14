import os

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session

from . import models
from .config import settings

dir_name = os.path.dirname(__file__)
firebaseServiceAccountCredentialsPath = os.path.join(
    dir_name, settings.FIREBASE_SERVICE_ACCOUNT_CREDENTIALS_PATH
)

cred = credentials.Certificate(firebaseServiceAccountCredentialsPath)
firebase_admin.initialize_app(cred)


def send_multicast_message(
        *,
        db: Session,
        fcm_tokens_db: list[models.FcmToken],
        title: str,
        msg: str,
        fcm_tokens: list[str],
        data_object: object | None = None
) -> None:
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=msg),
        data=data_object,
        tokens=fcm_tokens,
        android=messaging.AndroidConfig(
            priority="high", notification=messaging.AndroidNotification(priority="max")
        ),
        apns=messaging.APNSConfig(
            headers={"apns-priority": "10", "interruption-level": "time-sensitive"}
        ),
    )

    response = messaging.send_each_for_multicast(message)

    db = db.object_session(fcm_tokens_db[0])

    if response.failure_count > 0:
        responses = response.responses
        for idx, resp in enumerate(responses):
            if not resp.success:
                # The order of responses corresponds to the order of the registration
                # tokens.
                db.delete(fcm_tokens_db[idx])  # todo: test

        db.commit()
