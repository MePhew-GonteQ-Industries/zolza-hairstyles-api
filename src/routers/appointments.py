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
from ..schemas.appointment import AppointmentSlot, CreateAppointment
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
                .where(models.HolidayTranslations.holiday_id == slot.holiday_info.id)
                .where(models.HolidayTranslations.language_id == user_language_id)
                .first()[0]
            )

            holiday_name = holiday_name
            slot.holiday_name = holiday_name

    return slots


@router.get("/mine")
def get_your_appointments(
    db: Session = Depends(get_db), user_session=Depends(oauth2.get_user)
):
    user = user_session.user

    appointments_db = (
        db.query(models.Appointment).where(models.Appointment.user_id == user.id).all()
    )

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
    verified_user = verified_user_session.verified_user

    service_db = (
        db.query(models.Service).where(models.Service == appointment.service_id).first()
    )
    available_slots = db.query(models.AppointmentSlot).where(
        models.AppointmentSlot.date
    )

    new_appointment = models.Appointment()

    scheduler.add_job(
        send_appointment_reminder,
        trigger="date",
        id=str(uuid.uuid4()),
        name=f"Appointment Reminder - User #{verified_user.id}",
        misfire_grace_time=20,
        next_run_time=datetime.datetime.now() + timedelta(days=-2),
    )
    raise NotImplementedError


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
    appointment_id: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_admin)
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
