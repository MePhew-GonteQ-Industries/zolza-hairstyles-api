from uuid import uuid4

from . import models
from .email_manager import send_email
from .fcm_manager import send_multicast_message


def send_appointment_reminder(
    get_db_func: callable, *, user_id: uuid4, appointment_id: uuid4
):
    print("RUNNING")
    db = next(get_db_func())

    user = db.query(models.User).where(models.User.id == user_id).first()

    # send email
    # send_email()

    # send push notifications
    send_multicast_message(
        title="Upcoming appointment",
        msg="Your appointment will take place in 2 hours",
        registration_tokens=[
            "dbHgCNb4SBCCJVMZDL3HxD:APA91bG9sz9AgyW516dOH2qKuoyZ7p9gcB7uL-REXOHcaIak3kf7CCVxGop6C2tQJuvuDXsg4OJY81FlGcrkzQdl6UxZA7zGgu2WqcaVrt-rbG4mXB9MpnFaEdPDhoN0nEjbaQtm7pbU"
        ],
    )
    print("DONE")


def test():
    print("TEST")
    send_multicast_message(
        title="Upcoming appointment",
        msg="Your appointment will take place in 2 hours",
        registration_tokens=[
            "d5jpl8DwTSmKiYww1LpvEO:APA91bFQ36fH34DXeyYzHLX37bg-4c32LMMb_o29uC2rz0_-MNxM2KjfyvButtMgo5znV7ORiDH43uOfUEwNf_b_jvUuULMNEmQfnGhjAUXEkbFtyYrsmPoUQE8sd8Efq1NoqRsKQEKh"
        ],
    )
