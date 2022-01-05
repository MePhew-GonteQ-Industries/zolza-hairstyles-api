from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix=settings.BASE_URL + '/services',
                   tags=['Services'])


@router.get('')
async def get_services():
    return {'service': {
        'id': '',
        'price': '5'
    }}
