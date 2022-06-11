from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..schemas.notifications import FcmToken

router = APIRouter(prefix=settings.BASE_URL + "/notifications", tags=["Notifications"])


@router.post(
    "/add_token",
)  # response_model=
def add_token(
    fcm_token: FcmToken,
    db: Session = Depends(get_db),
    user_session=Depends(oauth2.get_user),
):
    user = user_session.user
    session = user_session.session

    fcm_token_db = models.FcmToken(
        token=fcm_token.fcm_token, user_id=user.id, session_id=session.id
    )
    db.add(fcm_token_db)
    db.commit()
