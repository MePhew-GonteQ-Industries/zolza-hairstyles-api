from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router = APIRouter(prefix=settings.BASE_URL + '/auth',
                   tags=['Authorization'])


@router.post('/login')
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return user_credentials


@router.get('')
async def authorized():
    return {'authorized': 'false',
            'permission_level': 'none'}
