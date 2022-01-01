from fastapi import APIRouter, status
from ..config import settings
from ..schemas.user_settings import BaseUserSettings

router = APIRouter(prefix=settings.BASE_URL + '/settings',
                   tags=['Settings'])


@router.get('/')
async def get_settings():
    return {'language': 'en-GB',
            'prefered_theme': 'dark'}


@router.post('/', status_code=status.HTTP_201_CREATED)
async def update_settings(user_settings: BaseUserSettings):
    return {'language': user_settings.language,
            'prefered_theme': user_settings.prefered_theme}
