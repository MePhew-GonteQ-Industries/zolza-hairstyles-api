from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix=settings.BASE_URL + '/auth',
                   tags=['Authorization'])


@router.get('/')
async def authorized():
    return {'authorized': 'false',
            'permission_level': 'none'}
