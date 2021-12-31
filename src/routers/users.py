from fastapi import APIRouter, status
from ..config import settings

router = APIRouter(prefix=settings.BASE_URL + '/users',
                   tags=['Users'])


@router.get('/me')
async def me():
    return {'test': 'success'}


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user():
    return {'s': 'sda'}
