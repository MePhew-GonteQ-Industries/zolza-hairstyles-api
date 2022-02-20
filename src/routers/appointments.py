import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..jobs import send_appointment_remainder
from ..scheduler import scheduler

router = APIRouter(prefix=settings.BASE_URL + "/appointments", tags=["Appointments"])


@router.get('/mine')
def get_your_appointments(db: Session = Depends(get_db),
                          user=Depends(oauth2.get_user)):
    appointments_db = db.query(models.Appointment).where(models.Appointment.user_id == user.id).all()

    return {'appointments': appointments_db}


@router.get('/mine/{id}')
def get_your_appointment(db: Session = Depends(get_db),
                         user=Depends(oauth2.get_verified_user)):
    return NotImplementedError


@router.put('/mine/{id}', status_code=status.HTTP_201_CREATED)
async def update_your_appointment(db: Session = Depends(get_db),
                                  user=Depends(oauth2.get_verified_user)):
    raise NotImplementedError


@router.post('', status_code=status.HTTP_201_CREATED)
def create_appointment(db: Session = Depends(get_db),
                       user=Depends(oauth2.get_verified_user)):

    scheduler.add_job(send_appointment_remainder, trigger='date',
                      id=str(uuid.uuid4()),
                      name=f'Appointment Remainder User {user.id}',
                      misfire_grace_time=20,
                      next_run_time=datetime.now() + timedelta(days=-2))
    raise NotImplementedError


@router.get('/all')
def get_all_appointments(db: Session = Depends(get_db),
                         user=Depends(oauth2.get_admin)):
    raise NotImplementedError


@router.get('/any/{id}')
async def get_any_appointment(db: Session = Depends(get_db),
                              user=Depends(oauth2.get_admin)):
    raise NotImplementedError


@router.put('/any/{id}')
def update_any_appointment(db: Session = Depends(get_db),
                           user=Depends(oauth2.get_admin)):
    raise NotImplementedError
