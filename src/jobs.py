from uuid import uuid4

from . import models
from .email_manager import send_email
from .fcm_manager import send_multicast_message


def send_appointment_reminder(
    get_db_func: callable, *, user_id: uuid4, appointment_id: uuid4
):
    db = next(get_db_func())

    user = db.query(models.User).where(models.User.id == user_id).first()

    appointment = (
        db.query(models.Appointment)
        .where(models.Appointment.id == appointment_id)
        .first()
    )

    user_notification_settings = (
        db.query(models.Setting)
        .where(models.Setting.user_id == user_id)
        .where(models.Setting.name == "notifications")
        .all()
    )

    # send email

    # send_email()

    # send push notifications

    user_fcm_registration_tokens = (
        db.query(models.FcmToken).where(models.FcmToken.user_id == user_id).all()
    )

    tokens = [token_db.token for token_db in user_fcm_registration_tokens]

    send_multicast_message(
        db=db,
        registration_tokens_db=user_fcm_registration_tokens,
        title="Upcoming appointment",
        msg="Your appointment will take place in 2 hours",
        registration_tokens=tokens,
    )
