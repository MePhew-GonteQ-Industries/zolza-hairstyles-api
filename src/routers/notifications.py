import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..schemas.notifications import FcmToken, ReturnFcmToken

router = APIRouter(prefix=settings.BASE_URL + "/notifications", tags=["Notifications"])


@router.post("/add_token", response_model=ReturnFcmToken)
def add_token(
        fcm_token: FcmToken,
        db: Session = Depends(get_db),
        user_session=Depends(oauth2.get_user),
):
    user = user_session.user
    session = user_session.session

    existing_token = (
        db.query(models.FcmToken)
        .where(models.FcmToken.user_id == user.id)
        .where(models.FcmToken.token == fcm_token.fcm_token)  # noqa
        .first()
    )

    if existing_token:
        return {
            "fcm_token": existing_token.token,
            "updated_at": existing_token.last_updated_at,
        }

    existing_session = (
        db.query(models.FcmToken)
        .where(models.FcmToken.user_id == user.id)
        .where(models.FcmToken.session_id == session.id)
        .first()
    )

    if existing_session:
        existing_session.token = fcm_token.fcm_token
        existing_session.last_updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing_session)

        return {
            "fcm_token": existing_session.token,
            "updated_at": existing_session.last_updated_at,
        }

    fcm_token_db = models.FcmToken(
        token=fcm_token.fcm_token, user_id=user.id, session_id=session.id
    )
    db.add(fcm_token_db)
    db.commit()
    db.refresh(fcm_token_db)

    return {"fcm_token": fcm_token_db.token, "updated_at": fcm_token_db.last_updated_at}
