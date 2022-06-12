import os

import firebase_admin
from firebase_admin import credentials, messaging

from .config import settings

dir_name = os.path.dirname(__file__)
print(dir_name)
firebaseServiceAccountCredentialsPath = os.path.join(
    dir_name, settings.FIREBASE_SERVICE_ACCOUNT_CREDENTIALS_PATH
)
print(firebaseServiceAccountCredentialsPath)

cred = credentials.Certificate(firebaseServiceAccountCredentialsPath)
firebase_admin.initialize_app(cred)


def send_multicast_message(
    title: str, msg: str, registration_tokens: list, data_object: object = None
):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=msg),
        data=data_object,
        tokens=registration_tokens,
    )

    response = messaging.send_multicast(message)
    print(f"Successfully sent message: {response}")

    return f"Successfully sent message: {response}"
