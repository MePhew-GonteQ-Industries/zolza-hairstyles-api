from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..schemas.user_settings import ReturnSettings, UpdateSettings

router = APIRouter(prefix=settings.BASE_URL + "/settings", tags=["Settings"])


@router.get("", response_model=ReturnSettings)
def get_settings(db: Session = Depends(get_db), user_session=Depends(oauth2.get_user)):
    user = user_session.user

    user_settings = (
        db.query(models.Setting).where(models.Setting.user_id == user.id).all()
    )

    return {"settings": user_settings}


@router.put("", response_model=ReturnSettings)
def update_settings(
    new_settings: UpdateSettings,
    db: Session = Depends(get_db),
    user_session=Depends(oauth2.get_user),
):
    user = user_session.user

    settings_db = []

    for setting in new_settings.settings:
        setting_db = (
            db.query(models.Setting)
            .where(models.Setting.user_id == user.id)
            .where(models.Setting.name == setting.name)
            .first()
        )

        setting_db.current_value = setting.new_value

        db.commit()

        settings_db.append(setting_db)

    for setting_db in settings_db:
        db.refresh(setting_db)

    return {"settings": settings_db}
