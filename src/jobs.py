import datetime

from pydantic import UUID4

from .notifications_manager import (
    AppointmentCanceledNotification, AppointmentUpdatedNotification,
    NewAppointmentNotification,
    UpcomingAppointmentNotification
)


def send_upcoming_appointment_notification(
        get_db_func: callable,
        *,
        user_id: UUID4,
        appointment_id: UUID4,
        minutes_to_appointment: int,
):
    db = next(get_db_func())

    upcoming_appointment_notification = UpcomingAppointmentNotification(
        db=db,
        user_id=user_id,
        appointment_id=appointment_id,
        minutes_to_appointment=minutes_to_appointment,
    )
    upcoming_appointment_notification.send()


def send_new_appointment_notification(
        get_db_func: callable,
        *,
        user_name: str,
        user_surname: str,
        service_id: UUID4,
        appointment_date: datetime.datetime,
):
    db = next(get_db_func())

    new_appointment_notification = NewAppointmentNotification(
        db=db,
        user_name=user_name,
        user_surname=user_surname,
        service_id=service_id,
        appointment_date=appointment_date,
    )
    new_appointment_notification.send()


def send_appointment_updated_notification(
        get_db_func: callable,
        *,
        user_id: UUID4,
        service_id: UUID4,
        new_appointment_date: datetime.datetime,
):
    db = next(get_db_func())

    appointment_updated_notification = AppointmentUpdatedNotification(
        db=db,
        user_id=user_id,
        service_id=service_id,
        new_appointment_date=new_appointment_date,
    )
    appointment_updated_notification.send()


def send_appointment_canceled_notification(
        get_db_func: callable,
        *,
        user_id: UUID4,
        service_id: UUID4,
        appointment_date: datetime.datetime,
):
    db = next(get_db_func())

    appointment_canceled_notification = AppointmentCanceledNotification(
        db=db,
        user_id=user_id,
        service_id=service_id,
        appointment_date=appointment_date,
    )
    appointment_canceled_notification.send()
