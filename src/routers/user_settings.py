from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..schemas.user_settings import ReturnSettings, UpdateSettings

router = APIRouter(prefix=settings.BASE_URL + '/settings',
                   tags=['Settings'])


@router.get('', response_model=ReturnSettings)
async def get_settings(db: Session = Depends(get_db),
                       user=Depends(oauth2.get_user)):
    user_settings = db.query(models.Setting).where(models.Setting.user_id == user.id).all()

    return {'settings': user_settings}


@router.put('')  # , response_model=ReturnSettings
async def update_settings(new_settings: UpdateSettings,
                          db: Session = Depends(get_db),
                          user=Depends(oauth2.get_user)):

    settings_db = []

    for setting in new_settings.settings:
        setting_db = db.query(models.Setting).where(models.Setting.user_id == user.id
                                                    and models.Setting.name == setting.get('name')).first()
        setting_db.current_value = setting.get('current_value')

        db.commit()
        db.refresh(setting_db)
        settings_db.append(setting_db)

    return {'settings': settings_db}
