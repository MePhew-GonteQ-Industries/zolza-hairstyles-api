import abc
import datetime
from typing import TypedDict

from pydantic import UUID4
from sqlalchemy.orm import Session

from src import models
from src.fcm_manager import send_multicast_message
from src.utils import get_user_language_id


class Notification:
    db: Session
    abort_send: bool
    fcm_tokens_db: list[models.FcmToken]
    fcm_tokens: list[str]
    title: str
    msg: str

    @abc.abstractmethod
    def send(self) -> None:
        if not self.abort_send:
            send_multicast_message(
                db=self.db,
                fcm_tokens_db=self.fcm_tokens_db,
                title=self.title,
                msg=self.msg,
                fcm_tokens=self.fcm_tokens,
            )

            # TODO: send email


class UpcomingAppointmentNotification(Notification):
    user_id: UUID4
    appointment_id: UUID4
    minutes_to_appointment: int

    user: models.User
    appointment: models.Appointment

    def __init__(self, *,
                 db: Session,
                 user_id: UUID4,
                 appointment_id: UUID4,
                 minutes_to_appointment: int,
                 ):
        self.db = db
        self.user_id = user_id
        self.appointment_id = appointment_id
        self.minutes_to_appointment = minutes_to_appointment

        self.fcm_tokens_db = (
            db.query(models.FcmToken).where(
                models.FcmToken.user_id == self.user_id
            ).all()
        )

        if self.fcm_tokens_db:
            self.fcm_tokens = [token_db.token for token_db in self.fcm_tokens_db]

            self.user = db.query(models.User).where(models.User.id == user_id).first()

            self.appointment = (
                db.query(models.Appointment)
                .where(models.Appointment.id == appointment_id)
                .first()
            )

            # TODO: Notification settings
            # user_notification_settings = (
            #     db.query(models.Setting)
            #     .where(models.Setting.user_id == user_id)
            #     .where(models.Setting.name == "notifications")
            #     .all()
            # )

            # TODO: translations
            # match self.content_language:
            #     case DefaultContentLanguages.polish:
            #         self.title = "Nadchodząca wizyta"
            #         self.msg = f"Wizyta rozpocznie się za {} "
            #     case DefaultContentLanguages.english:
            #         self.title = "Upcoming appointment"
            #         self.msg = f"Your appointment will take place in {}"
            #     case _:
            #         raise ValueError()

            service_db = db.query(models.Service).where(
                models.Service.id == self.appointment.service_id).first()

            language_id = get_user_language_id(db, self.user.id)

            service_translation = (
                db.query(
                    models.ServiceTranslations.name,
                    models.ServiceTranslations.description
                )
                .where(models.ServiceTranslations.language_id == language_id)
                .where(models.ServiceTranslations.service_id == service_db.id)
                .first()
            )
            service_name = service_translation[0]

            self.title = service_name

            match minutes_to_appointment:
                case 30:
                    self.msg = f"Twoja wizyta odbędzie się za" \
                               f" 30 minut"
                case 120:
                    self.msg = f"Twoja wizyta odbędzie się za" \
                               f" 2 godziny"
        else:
            self.abort_send = True

    def send(self) -> None:
        super().send()


class AppointmentUpdatedNotification(Notification):
    user_id: UUID4

    def __init__(self,
                 *,
                 db: Session,
                 user_id: UUID4,
                 service_id: UUID4,
                 new_appointment_date: datetime.datetime,
                 ):
        self.db = db

        self.fcm_tokens_db = (
            db.query(models.FcmToken).where(
                models.FcmToken.user_id == user_id
            ).all()
        )

        # TODO: Notification settings

        if self.fcm_tokens_db:
            self.fcm_tokens = [token_db.token for token_db in self.fcm_tokens_db]

            language_id = get_user_language_id(db, user_id)

            service_translation = (
                db.query(
                    models.ServiceTranslations.name,
                    models.ServiceTranslations.description
                )
                .where(models.ServiceTranslations.language_id == language_id)
                .where(models.ServiceTranslations.service_id == service_id)
                .first()
            )
            service_name = service_translation[0]

            self.title = service_name
            self.msg = f"Zmieniono datę wizyty na {new_appointment_date}"

        else:
            self.abort_send = True

    def send(self) -> None:
        super().send()


class AppointmentCanceledNotification(Notification):
    user_id: UUID4

    def __init__(self,
                 *,
                 db: Session,
                 user_id: UUID4,
                 service_id: UUID4,
                 appointment_date: datetime.datetime,
                 ):
        self.db = db

        self.fcm_tokens_db = (
            db.query(models.FcmToken).where(
                models.FcmToken.user_id == user_id
            ).all()
        )

        # TODO: Notification settings

        if self.fcm_tokens_db:
            self.fcm_tokens = [token_db.token for token_db in self.fcm_tokens_db]

            language_id = get_user_language_id(db, user_id)

            service_translation = (
                db.query(
                    models.ServiceTranslations.name,
                    models.ServiceTranslations.description
                )
                .where(models.ServiceTranslations.language_id == language_id)
                .where(models.ServiceTranslations.service_id == service_id)
                .first()
            )
            service_name = service_translation[0]

            self.title = service_name
            self.msg = f"Wizyta ({appointment_date}) została odwołana"

        else:
            self.abort_send = True

    def send(self) -> None:
        super().send()


class NewAppointmentNotification(Notification):
    user_name: str
    user_surname: str
    service_id: UUID4
    appointment_date: datetime.datetime

    class Notification(TypedDict):
        fcm_tokens_db: list[models.FcmToken]
        fcm_tokens: list[str]
        title: str
        msg: str

    notifications: list[Notification]

    def __init__(self,
                 *,
                 db: Session,
                 user_name: str,
                 user_surname: str,
                 service_id: UUID4,
                 appointment_date: datetime.datetime,
                 ):
        self.user_name = user_name
        self.user_surname = user_surname
        self.service_id = service_id
        self.appointment_date = appointment_date

        # TODO: Notification settings

        notification_recipients = (
            db.query(models.User).where(
                'owner' in models.User.permission_level
            ).all()
        )

        if notification_recipients:
            service_db = db.query(models.Service).where(
                models.Service.id == self.service_id).first()

            for recipient in notification_recipients:
                recipient_fcm_tokens_db = db.query(
                    models.FcmToken
                ).where(
                    models.FcmToken.user_id == recipient.id
                )

                if recipient_fcm_tokens_db:
                    recipient_fcm_tokens = [
                        token_db.token for token_db in recipient_fcm_tokens_db
                    ]

                    language_id = get_user_language_id(db, recipient.id)

                    service_translation = (
                        db.query(
                            models.ServiceTranslations.name,
                            models.ServiceTranslations.description
                        )
                        .where(models.ServiceTranslations.language_id == language_id)
                        .where(models.ServiceTranslations.service_id == service_db.id)
                        .first()
                    )
                    service_name = service_translation[0]

                    title = f"{self.user_name} {self.user_surname} umówił/a wizytę"
                    msg = f"{service_name} - {self.appointment_date}"

                    self.notifications.append({
                        'fcm_tokens_db': recipient_fcm_tokens_db,
                        'fcm_tokens': recipient_fcm_tokens,
                        'title': title,
                        'msg': msg,
                    })

        else:
            self.abort_send = True

    def send(self) -> None:
        if not self.abort_send:
            for notification in self.notifications:
                send_multicast_message(
                    db=self.db,
                    fcm_tokens_db=notification.get('fcm_tokens_db'),
                    title=notification.get('title'),
                    msg=notification.get('msg'),
                    fcm_tokens=notification.get('fcm_tokens'),
                )

                # TODO: send email
