from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix=settings.BASE_URL + '/appointments',
                   tags=['Appointments'])


@router.get('/')
async def get_appointments():
    return {'appointment': {
        'id': 0,
        'type': '',
        'time': '15-1512515-12512512-251',
        'created_at': '124-4124-4241',
        'user_id': 5
        },
    }
