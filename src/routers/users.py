from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix=settings.BASE_URL + '/users',
                   tags=['Users'])


@router.get('/')
async def me():
    return {'test': 'success'}
