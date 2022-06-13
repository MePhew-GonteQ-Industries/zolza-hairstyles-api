import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..jobs import send_appointment_reminder, test
from ..scheduler import scheduler, test_sch
from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..schemas.notifications import FcmToken

router = APIRouter(prefix=settings.BASE_URL + "/notifications", tags=["Notifications"])


@router.post("/add_token", response_model=FcmToken)
def add_token(
    fcm_token: FcmToken,
    db: Session = Depends(get_db),
    user_session=Depends(oauth2.get_user),
):
    user = user_session.user
    session = user_session.session

    fcm_token_db = (
        db.query(models.FcmToken)
        .where(models.FcmToken.user_id == user.id)
        .where(models.FcmToken.session_id == user_session.id)
        .first()
    )

    if fcm_token_db:
        fcm_token_db.last_updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(fcm_token_db)
        return fcm_token_db

    fcm_token_db = models.FcmToken(
        token=fcm_token.fcm_token, user_id=user.id, session_id=session.id
    )
    db.add(fcm_token_db)
    db.commit()
    db.refresh(fcm_token_db)

    return fcm_token_db


# DEBUG todo: REMOVE
@router.post("/send_notification")
def send_notification():
    print(scheduler.running)
    test_sch()

    scheduler.add_job(
        send_appointment_reminder,
        # test,
        trigger="date",
        id=f"Appointment Reminder - Appointment #2141412421",
        name=f"Appointment Reminder - Appointment #2141412421",
        run_date=datetime.datetime.now(),
        args=[get_db],
        kwargs={"user_id": "sadasda2dazs", "appointment_id": "124124rfdsa214rqfwa"},
    )
    # print(scheduler.get_jobs()[0])
