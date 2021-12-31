from fastapi import APIRouter, status
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


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_appointment():
    return {'': ''}


@router.get('/{id}', status_code=status.HTTP_201_CREATED)
async def get_appointment():
    pass


@router.post('/{id}', status_code=status.HTTP_201_CREATED)
async def update_appointment():
    pass
