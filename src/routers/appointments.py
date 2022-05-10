import uuid
from datetime import timedelta
import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..exceptions import ResourceNotFoundHTTPException
from ..jobs import send_appointment_reminder
from ..scheduler import scheduler
from ..schemas.appointment import AppointmentSlot, CreateAppointment, ReturnAppointments
from ..utils import get_user_language_id

router = APIRouter(prefix=settings.BASE_URL + "/appointments", tags=["Appointments"])


@router.get("/slots", response_model=list[AppointmentSlot])
def get_appointment_slots(
        date: datetime.date | None = None,
        db: Session = Depends(get_db),
        user_session=Depends(oauth2.get_user),
):
    now = datetime.date.today()
    last_available_date = now + timedelta(days=settings.MAX_FUTURE_APPOINTMENT_DAYS)

    slots = db.query(models.AppointmentSlot)

    if date:
        if date > last_available_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        slots = slots.where(models.AppointmentSlot.date == date)
    else:
        slots = slots.where(models.AppointmentSlot.date <= last_available_date)

    slots = slots.order_by(models.AppointmentSlot.start_time).all()

    user_language_id = get_user_language_id(db, user_session.user.id)

    for slot in slots:
        if slot.holiday:
            holiday_name = (
                db.query(models.HolidayTranslations.name)
                    .where(
                    models.HolidayTranslations.holiday_id == slot.holiday_info.id)
                    .where(models.HolidayTranslations.language_id == user_language_id)
                    .first()[0]
            )

            holiday_name = holiday_name
            slot.holiday_name = holiday_name

    return slots


@router.get("/mine", response_model=ReturnAppointments)
def get_your_appointments(
        db: Session = Depends(get_db), user_session=Depends(oauth2.get_user)
):
    user = user_session.user

    appointments_db = (
        db.query(models.Appointment).where(models.Appointment.user_id == user.id).all()
    )

    language_id = get_user_language_id(db, user.id)

    for appointment in appointments_db:
        service_translation = (
            db.query(models.ServiceTranslations.name,
                     models.ServiceTranslations.description).where(
                models.ServiceTranslations.language_id == language_id).where(
                models.ServiceTranslations.service_id == appointment.service.id
            ).first()
        )
        appointment.service.name = service_translation[0]
        appointment.service.description = service_translation[1]

    return {"appointments": appointments_db}


@router.get("/mine/{id}")
def get_your_appointment(
        db: Session = Depends(get_db),
        verified_user_session=Depends(oauth2.get_verified_user),
):
    verified_user = verified_user_session.verified_user

    appointment_db = db.query(models.Appointment).where(
        models.Appointment.user_id == verified_user.id
    )

    return appointment_db


@router.put("/mine/{id}", status_code=status.HTTP_201_CREATED)
async def update_your_appointment(
        db: Session = Depends(get_db),
        verified_user_session=Depends(oauth2.get_verified_user),
):
    raise NotImplementedError


@router.post("", status_code=status.HTTP_201_CREATED)
def create_appointment(
        appointment: CreateAppointment,
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

    service_db = (
        db.query(models.Service)
            .where(models.Service.id == appointment.service_id)
            .first()
    )

    if not service_db:
        raise ResourceNotFoundHTTPException(
            detail=f"Service with id of {appointment.service_id} does not exist"
        )

    appointment_start_time = first_slot_db.start_time
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
            .order_by(models.AppointmentSlot.start_time)
            .all()
    )

    if not len(available_slots) == required_slots:
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
    db.commit()
    db.refresh(new_appointment)

    for slot in available_slots:
        slot.occupied = True
        slot.occupied_by_appointment = new_appointment.id
        db.commit()

    scheduler.add_job(
        send_appointment_reminder,
        trigger="date",
        id=f"Appointment Reminder - Appointment #{new_appointment.id}",
        name=f"Appointment Reminder - Appointment #{new_appointment.id}",
        misfire_grace_time=20,
        next_run_time=datetime.datetime.now() + timedelta(days=-2),
    )

    return new_appointment


@router.get("/all")
def get_all_appointments(
        db: Session = Depends(get_db),
        _=Depends(oauth2.get_admin),
        upcoming_only: bool = False,
        offset: int = 0,
        limit: int | None = None,
        user_id: UUID4 | None = None,
):
    all_appointments = db.query(models.Appointment)

    if upcoming_only:
        all_appointments = all_appointments.where(models.Appointment.archival == False)

    if user_id:
        all_appointments = all_appointments.where(models.Appointment.user_id == user_id)

    if offset:
        all_appointments = all_appointments.offset(offset)

    if limit:
        all_appointments = all_appointments.limit(limit)

    all_appointments = all_appointments.all()

    return all_appointments


@router.get("/any/{id}")
async def get_any_appointment(
        appointment_id: UUID4, db: Session = Depends(get_db),
        _=Depends(oauth2.get_admin)
):
    appointment = (
        db.query(models.Appointment)
            .where(models.Appointment.id == appointment_id)
            .first()
    )

    if not appointment:
        raise ResourceNotFoundHTTPException()

    return appointment


@router.put("/any/{id}")
def update_any_appointment(
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

    # TODO: Update appointment

    return appointment_db
