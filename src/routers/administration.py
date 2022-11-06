from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..schemas.administration import ServiceStats

router = APIRouter(
    prefix=settings.BASE_URL + "/administration", tags=["Administration"]
)


def modify_working_hours():
    raise NotImplementedError


def add_appointment_slot():
    raise NotImplementedError


@router.post("/get-stats", response_model=ServiceStats)
def get_stats(db: Session = Depends(get_db), _=Depends(oauth2.get_admin)):
    registered_users = db.query(models.User.id).count()

    upcoming_appointments = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.end_slot.has(
                models.AppointmentSlot.end_time > datetime.utcnow()
            )
        )
        .count()
    )

    archival_appointments = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.end_slot.has(
                models.AppointmentSlot.end_time < datetime.utcnow()
            )
        )
        .count()
    )

    total_appointments = db.query(models.Appointment).count()

    return {
        "registered_users": registered_users,
        "total_appointments": total_appointments,
        "upcoming_appointments": upcoming_appointments,
        "archival_appointments": archival_appointments,
    }
