from fastapi import APIRouter, status, Depends
from ..config import settings
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.user import BaseUser, CreateUser
from .. import models

router = APIRouter(prefix=settings.BASE_URL + '/users',
                   tags=['Users'])


@router.post('/{s}', status_code=status.HTTP_201_CREATED, response_model=BaseUser)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get('/me')
async def me(db: Session = Depends(get_db)):
    return {'test': 'success'}
