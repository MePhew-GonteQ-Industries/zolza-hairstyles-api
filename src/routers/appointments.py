import datetime
import logging
from datetime import timedelta

import apscheduler.jobstores.base
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, status
from pydantic import UUID4
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql import extract

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..exceptions import ResourceNotFoundHTTPException
from ..jobs import (
    send_appointment_canceled_notification,
    send_appointment_updated_notification,
    send_new_appointment_notification,
    send_upcoming_appointment_notification,
)
from ..scheduler import scheduler
from ..schemas.appointment import (
    AppointmentSlot,
    CreateAppointment,
    FirstSlot,
    ReserveSlots,
    ReturnAllAppointments,
    ReturnAppointment,
    ReturnAppointmentDetailed,
    UnreserveSlots,
)
from ..utils import (
    PL_TIMEZONE,
    get_language_code_from_header,
    get_language_id_from_language_code,
    get_user_language_id,
    is_archival,
)

router = APIRouter(prefix=settings.BASE_URL + "/appointments", tags=["Appointments"])


@router.get("/slots", response_model=list[AppointmentSlot])
def get_appointment_slots(
    db: Session = Depends(get_db),
    date: datetime.date | None = None,
    accept_language: str | None = Header(None),
):
    today = datetime.date.today()
    first_available_time = datetime.datetime.now(PL_TIMEZONE) + timedelta(hours=1)
    last_available_day = today + timedelta(days=settings.MAX_FUTURE_APPOINTMENT_DAYS)

    slots = db.query(models.AppointmentSlot)

    if date:
        if date > last_available_day:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        slots = slots.where(models.AppointmentSlot.date == date).where(
            (models.AppointmentSlot.start_time == None)
            | (models.AppointmentSlot.start_time > first_available_time)
        )
    else:
        slots = slots.where(
            (
                (models.AppointmentSlot.start_time == None)
                & (models.AppointmentSlot.date > first_available_time)
            )
            | (models.AppointmentSlot.start_time > first_available_time)
        ).where(models.AppointmentSlot.date <= last_available_day)

    slots = slots.order_by(
        models.AppointmentSlot.date,
        models.AppointmentSlot.start_time,
    ).all()

    language_code = get_language_code_from_header(accept_language)
    user_language_id = get_language_id_from_language_code(db, language_code)

    for slot in slots:
        if slot.holiday:
            holiday_name = (
                db.query(models.HolidayTranslations.name)
                .where(models.HolidayTranslations.holiday_id == slot.holiday_info.id)
                .where(models.HolidayTranslations.language_id == user_language_id)
                .first()[0]
            )

            slot.holiday_name = holiday_name

    return slots


@router.get("/nearest/{service_id}", response_model=list[AppointmentSlot])
def get_nearest_slots(
    service_id: UUID4,
    db: Session = Depends(get_db),
    limit: int = 9,
):
    service_db = db.query(models.Service).where(models.Service.id == service_id).first()

    if not service_db:
        raise ResourceNotFoundHTTPException(
            detail=f"Service with id of {service_id} was not found"
        )

    required_slots = service_db.required_slots

    now = datetime.date.today()
    first_available_time = datetime.datetime.utcnow() + timedelta(hours=1)
    last_available_date = now + timedelta(days=settings.MAX_FUTURE_APPOINTMENT_DAYS)

    slots_db = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.holiday == False)
        .where(models.AppointmentSlot.sunday == False)
        .where(
            (
                (models.AppointmentSlot.start_time == None)
                & (models.AppointmentSlot.date > first_available_time)  # noqa
            )
            | (models.AppointmentSlot.start_time > first_available_time)
        )
        .where(models.AppointmentSlot.date <= last_available_date)
        .order_by(
            models.AppointmentSlot.date,
            models.AppointmentSlot.start_time,
        )
        .all()
    )

    slots = []

    for index, slot in enumerate(slots_db):
        free_slots_found = 0
        for slot_index in range(required_slots):
            if len(slots_db) > index + slot_index:
                next_slot = slots_db[index + slot_index]
                if (
                    not next_slot.occupied
                    and not next_slot.reserved
                    and not next_slot.break_time
                ):
                    free_slots_found += 1

            if free_slots_found == required_slots:
                slots.append(slot)

        if len(slots) == limit:
            break

    return slots


@router.get("/mine", response_model=list[ReturnAppointment])
def get_your_appointments(
    db: Session = Depends(get_db), user_session=Depends(oauth2.get_user)
):
    user = user_session.user

    appointments_db = (
        db.query(models.Appointment).where(models.Appointment.user_id == user.id).all()
    )

    language_id = get_user_language_id(db, user.id)

    for appointment_db in appointments_db:
        service_translation = (
            db.query(
                models.ServiceTranslations.name, models.ServiceTranslations.description
            )
            .where(models.ServiceTranslations.language_id == language_id)
            .where(models.ServiceTranslations.service_id == appointment_db.service.id)
            .first()
        )
        appointment_db.service.name = service_translation[0]
        appointment_db.service.description = service_translation[1]

        appointment_db.archival = is_archival(appointment_db)

    return appointments_db


@router.get("/mine/{id}")
def get_your_appointment(
    db: Session = Depends(get_db),
    verified_user_session=Depends(oauth2.get_verified_user),
):
    verified_user = verified_user_session.verified_user

    appointment_db = db.query(models.Appointment).where(
        models.Appointment.user_id == verified_user.id
    )

    language_id = get_user_language_id(db, verified_user.id)

    service_translation = (
        db.query(
            models.ServiceTranslations.name, models.ServiceTranslations.description
        )
        .where(models.ServiceTranslations.language_id == language_id)
        .where(models.ServiceTranslations.service_id == appointment_db.service.id)
        .first()
    )
    appointment_db.service.name = service_translation[0]
    appointment_db.service.description = service_translation[1]

    appointment_db.archival = is_archival(appointment_db)

    return appointment_db


@router.post("", status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment: CreateAppointment,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    verified_user_session=Depends(oauth2.get_verified_user),
):
    first_slot_db = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.id == appointment.first_slot_id)
        .first()
    )

    if not first_slot_db:
        raise ResourceNotFoundHTTPException(
            detail=f"Slot with id of {appointment.first_slot_id} does not exist"
        )

    appointment_start_time = first_slot_db.start_time

    now = datetime.datetime.now(PL_TIMEZONE)
    first_available_time = now + timedelta(hours=1)

    if appointment_start_time < first_available_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    today = datetime.date.today()
    last_available_day = today + timedelta(days=settings.MAX_FUTURE_APPOINTMENT_DAYS)

    if appointment_start_time.date() > last_available_day:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    service_db = (
        db.query(models.Service)
        .where(models.Service.id == appointment.service_id)
        .first()
    )

    if not service_db:
        raise ResourceNotFoundHTTPException(
            detail=f"Service with id of {appointment.service_id} does not exist"
        )

    required_slots = service_db.required_slots

    appointment_end_time = appointment_start_time + timedelta(
        minutes=settings.APPOINTMENT_SLOT_TIME_MINUTES * required_slots
    )

    available_slots = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.start_time >= appointment_start_time)
        .where(models.AppointmentSlot.end_time <= appointment_end_time)
        .where(models.AppointmentSlot.occupied == False)
        .where(models.AppointmentSlot.reserved == False)
        .where(models.AppointmentSlot.holiday == False)
        .where(models.AppointmentSlot.sunday == False)
        .where(models.AppointmentSlot.break_time == False)
        .where(extract("dow", models.AppointmentSlot.date) != 6)
        .order_by(models.AppointmentSlot.start_time)
        .all()
    )

    if len(available_slots) != required_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="not enough free slots available starting from slot "
            f"with id of {appointment.first_slot_id} to "
            "accommodate service with id of "
            f"{appointment.service_id} that requires "
            f"{required_slots} consecutive free slots",
        )

    verified_user = verified_user_session.verified_user

    new_appointment = models.Appointment(
        service_id=appointment.service_id,
        user_id=verified_user.id,
        start_slot_id=appointment.first_slot_id,
        end_slot_id=available_slots[-1].id,
    )

    db.add(new_appointment)
    db.flush()

    for slot in available_slots:
        slot.occupied = True
        slot.occupied_by_appointment = new_appointment.id

    if now < appointment_start_time - timedelta(hours=2):
        scheduler.add_job(
            func=send_upcoming_appointment_notification,
            trigger="date",
            id=f"appointment_reminder_t_minus_120_min_appointment#{new_appointment.id}",
            name=f"Appointment Reminder T-120min - Appointment #{new_appointment.id}",
            misfire_grace_time=20,
            next_run_time=appointment_start_time - timedelta(hours=2),
            args=[get_db],
            kwargs={
                "user_id": verified_user.id,
                "appointment_id": new_appointment.id,
                "minutes_to_appointment": 120,
            },
        )  # todo: fix possible error

    if now < appointment_start_time - timedelta(minutes=30):
        scheduler.add_job(
            func=send_upcoming_appointment_notification,
            trigger="date",
            id=f"appointment_reminder_t_minus_30_min_appointment#{new_appointment.id}",
            name=f"Appointment Reminder T-30min - Appointment #{new_appointment.id}",
            misfire_grace_time=20,
            next_run_time=appointment_start_time - timedelta(minutes=30),
            args=[get_db],
            kwargs={
                "user_id": verified_user.id,
                "appointment_id": new_appointment.id,
                "minutes_to_appointment": 30,
            },
        )  # todo: fix possible error

    new_appointment.archival = False

    background_tasks.add_task(
        send_new_appointment_notification,
        db,
        user_name=verified_user.name,
        user_surname=verified_user.surname,
        service_id=service_db.id,
        appointment_date=first_slot_db.start_time,
    )

    db.commit()
    db.refresh(new_appointment)

    return new_appointment


@router.get("/all", response_model=ReturnAllAppointments)
def get_all_appointments(
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),
    include_archival: bool = True,
    offset: int = 0,
    limit: int | None = None,
    user_id: UUID4 | None = None,
):
    admin = admin_session.admin

    appointments_db = db.query(models.Appointment)

    if not include_archival:
        appointments_db = appointments_db.where(
            models.Appointment.end_slot.end_time < datetime.datetime.now(PL_TIMEZONE)
        )

    if user_id:
        appointments_db = appointments_db.where(models.Appointment.user_id == user_id)

    if offset:
        appointments_db = appointments_db.offset(offset)

    if limit:
        appointments_db = appointments_db.limit(limit)

    appointments_db = appointments_db.all()

    appointments_num = db.query(models.Appointment).count()

    language_id = get_user_language_id(db, admin.id)

    for appointment_db in appointments_db:
        service_translation = (
            db.query(
                models.ServiceTranslations.name, models.ServiceTranslations.description
            )
            .where(models.ServiceTranslations.language_id == language_id)
            .where(models.ServiceTranslations.service_id == appointment_db.service.id)
            .first()
        )
        appointment_db.service.name = service_translation[0]
        appointment_db.service.description = service_translation[1]

        appointment_db.archival = is_archival(appointment_db)

    return {"items": appointments_db, "total": appointments_num}


@router.get("/any/{appointment_id}", response_model=ReturnAppointmentDetailed)
def get_any_appointment(
    appointment_id: UUID4,
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),
):
    appointment_db = (
        db.query(models.Appointment)
        .where(models.Appointment.id == appointment_id)
        .first()
    )

    if not appointment_db:
        raise ResourceNotFoundHTTPException()

    admin = admin_session.admin
    language_id = get_user_language_id(db, admin.id)

    service_translation = (
        db.query(
            models.ServiceTranslations.name, models.ServiceTranslations.description
        )
        .where(models.ServiceTranslations.language_id == language_id)
        .where(models.ServiceTranslations.service_id == appointment_db.service.id)
        .first()
    )
    appointment_db.service.name = service_translation[0]
    appointment_db.service.description = service_translation[1]

    appointment_db.archival = is_archival(appointment_db)

    return appointment_db


# TODO: find potential bug when checking free space
@router.put("/any/{appointment_id}")
def update_any_appointment(
    new_start_slot: FirstSlot,
    appointment_id: UUID4,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    appointment_db = (
        db.query(models.Appointment)
        .where(models.Appointment.id == appointment_id)
        .first()
    )

    if not appointment_db:
        raise ResourceNotFoundHTTPException()

    if is_archival(appointment_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit an archival resource",
        )

    first_slot_db = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.id == new_start_slot.first_slot_id)
        .first()
    )

    if not first_slot_db:
        raise ResourceNotFoundHTTPException(
            detail=f"Slot with id of {new_start_slot.first_slot_id} does not exist"
        )

    appointment_start_time = first_slot_db.start_time
    required_slots = appointment_db.service.required_slots
    appointment_end_time = appointment_start_time + timedelta(
        minutes=settings.APPOINTMENT_SLOT_TIME_MINUTES * required_slots
    )

    available_slots = db.query(models.AppointmentSlot).filter(
        and_(
            models.AppointmentSlot.start_time >= appointment_start_time,
            models.AppointmentSlot.end_time <= appointment_end_time,
            models.AppointmentSlot.reserved == False,
            models.AppointmentSlot.holiday == False,
            models.AppointmentSlot.sunday == False,
            models.AppointmentSlot.break_time == False,
            or_(
                models.AppointmentSlot.occupied_by_appointment != appointment_db.id,
                models.AppointmentSlot.occupied_by_appointment == None,
            ),
        )
    )

    available_slots = available_slots.all()

    if len(available_slots) < required_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="not enough free slots available starting from slot "
            f"with id of {new_start_slot.first_slot_id} to "
            "accommodate service with id of "
            f"{appointment_db.service.id} that requires "
            f"{required_slots} consecutive free slots",
        )

    appointment_db.start_slot_id = new_start_slot.first_slot_id
    appointment_db.end_slot_id = available_slots[-1].id

    db.commit()
    db.refresh(appointment_db)

    current_slots = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.occupied == True)
        .where(models.AppointmentSlot.occupied_by_appointment == appointment_db.id)
        .order_by(models.AppointmentSlot.start_time)
        .all()
    )

    for slot in current_slots:
        slot.occupied = False
        slot.occupied_by_appointment = None

    for slot in available_slots:
        slot.occupied = True
        slot.occupied_by_appointment = appointment_db.id

    db.commit()

    for job_name in [
        f"appointment_reminder_t_minus_120_min_appointment#{appointment_db.id}",
        f"appointment_reminder_t_minus_30_min_appointment#{appointment_db.id}",
    ]:
        try:
            scheduler.remove_job(job_name)
        except apscheduler.jobstores.base.JobLookupError:
            logging.info(
                f"Failed to remove job: {job_name}"
                f"Appointment reminder for appointment {appointment_db.id}"
            )

    scheduler.add_job(
        func=send_upcoming_appointment_notification,
        trigger="date",
        id=f"appointment_reminder_t_minus_120_min_appointment#{appointment_db.id}",
        name=f"Appointment Reminder T-120min - Appointment #{appointment_db.id}",
        misfire_grace_time=20,
        next_run_time=appointment_start_time - timedelta(hours=2),
        args=[get_db],
        kwargs={
            "user_id": appointment_db.id,
            "appointment_id": appointment_db.id,
            "minutes_to_appointment": 120,
        },
    )

    scheduler.add_job(
        func=send_upcoming_appointment_notification,
        trigger="date",
        id=f"appointment_reminder_t_minus_30_min_appointment#{appointment_db.id}",
        name=f"Appointment Reminder T-30min - Appointment #{appointment_db.id}",
        misfire_grace_time=20,
        next_run_time=appointment_start_time - timedelta(minutes=30),
        args=[get_db],
        kwargs={
            "user_id": appointment_db.id,
            "appointment_id": appointment_db.id,
            "minutes_to_appointment": 30,
        },
    )

    appointment_db.archival = False

    background_tasks.add_task(
        send_appointment_updated_notification,
        db,
        user_id=appointment_db.user.id,
        service_id=appointment_db.service.id,
        new_appointment_date=appointment_db.start_slot.start_time,
    )

    return appointment_db


@router.post("/any/{appointment_id}")
def cancel_appointment(
    appointment_id: UUID4,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    appointment_db = (
        db.query(models.Appointment)
        .where(models.Appointment.id == appointment_id)
        .first()
    )

    if not appointment_db:
        raise ResourceNotFoundHTTPException()

    if is_archival(appointment_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit an archived resource",
        )

    occupied_slots = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.occupied_by_appointment == appointment_id)
        .all()
    )

    for slot in occupied_slots:
        slot.occupied = False
        slot.occupied_by_appointment = None

    appointment_db.canceled = True

    db.commit()

    for job_name in [
        f"appointment_reminder_t_minus_120_min_appointment#{appointment_db.id}",
        f"appointment_reminder_t_minus_30_min_appointment#{appointment_db.id}",
    ]:
        try:
            scheduler.remove_job(job_name)
        except apscheduler.jobstores.base.JobLookupError:
            logging.info(
                f"Failed to remove job: {job_name}"
                f"Appointment reminder for appointment {appointment_db.id}"
            )

    appointment_db.archival = False

    background_tasks.add_task(
        send_appointment_canceled_notification,
        db,
        user_id=appointment_db.user.id,
        service_id=appointment_db.service.id,
        appointment_date=appointment_db.start_slot.start_time,
    )

    return appointment_db


@router.post("/reserve_slots")
def reserve_slots(
    reserve_slots_data: ReserveSlots,
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    slots_db = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.id.in_(reserve_slots_data.slots))
        .where(models.AppointmentSlot.reserved == False)
        .where(models.AppointmentSlot.occupied == False)
        .where(models.AppointmentSlot.holiday == False)
        .where(models.AppointmentSlot.sunday == False)
        .where(models.AppointmentSlot.break_time == False)
        .where(
            models.AppointmentSlot.start_time
            > datetime.datetime.now().astimezone(PL_TIMEZONE)
        )
        .all()
    )

    slots_db_ids = [slot_db.id for slot_db in slots_db]

    if len(slots_db) != len(reserve_slots_data.slots):
        invalid_slots = [
            str(slot) for slot in reserve_slots_data.slots if slot not in slots_db_ids
        ]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"These slots cannot be reserved: {invalid_slots}"
            f" (This most likely means these slots are either"
            f" already reserved or occupied, holiday, sunday, break time"
            f" or archival)",
        )

    for slot_db in slots_db:
        slot_db.reserved = True
        slot_db.reserved_reason = reserve_slots_data.reason

    db.commit()
    for slot_db in slots_db:
        db.refresh(slot_db)

    return {"status": "success", "reserved_slots": slots_db}


@router.post("/unreserve_slots")
def unreserve_slots(
    unreserve_slots_data: UnreserveSlots,
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    slots_db = (
        db.query(models.AppointmentSlot)
        .where(models.AppointmentSlot.id.in_(unreserve_slots_data.slots))
        .where(models.AppointmentSlot.reserved == True)
        .where(models.AppointmentSlot.occupied == False)
        .where(models.AppointmentSlot.holiday == False)
        .where(models.AppointmentSlot.sunday == False)
        .where(models.AppointmentSlot.break_time == False)
        .where(
            models.AppointmentSlot.start_time
            > datetime.datetime.now().astimezone(PL_TIMEZONE)
        )
        .all()
    )

    slots_db_ids = [slot_db.id for slot_db in slots_db]

    if len(slots_db) != len(unreserve_slots_data.slots):
        invalid_slots = [
            str(slot) for slot in unreserve_slots_data.slots if slot not in slots_db_ids
        ]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"These slots cannot be reserved: {invalid_slots}"
            f" (This most likely means these slots are either"
            f" not reserved or occupied, holiday, sunday, break time"
            f" or archival)",
        )

    for slot_db in slots_db:
        slot_db.reserved = False
        slot_db.reserved_reason = None

    db.commit()
    for slot_db in slots_db:
        db.refresh(slot_db)

    return {"status": "success", "unreserved_slots": slots_db}
