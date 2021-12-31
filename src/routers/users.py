from fastapi import APIRouter, status, Depends
from ..config import settings
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix=settings.BASE_URL + '/users',
                   tags=['Users'])


@router.get('/me')
async def me():
    return {'test': 'success'}


@router.post('/', status_code=status.HTTP_201_CREATED)
def create_user(db: Session = Depends(get_db)):
    return {'s': 'sda'}
