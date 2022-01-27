from jose import JWTError, jwt
from datetime import datetime, timedelta

from . import models
from .config import settings
from typing import Optional, Callable
from fastapi import Depends, status
from sqlalchemy.orm import Session
from .database import get_db
from fastapi.security import OAuth2PasswordBearer
from .schemas.oauth2 import CreateTokenPayload, ReturnAccessTokenPayload, ReturnGenericToken, ReturnTokenPayload, \
    TokenType
from .exceptions import AccountDisabledHTTPException, IncorrectTokenDataException, \
    InsufficientPermissionHTTPException, InvalidTokenException, \
    MalformedAccessTokenException, SessionNotFoundHTTPException, UnverifiedUserHTTPException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


def create_jwt(token_data: CreateTokenPayload):
    encode_data = {'sub': str(token_data.user_id),
                   'type': token_data.token_type}

    if token_data.token_type == TokenType.access_token or token_data.token_type == TokenType.refresh_token:
        if token_data.permission_level:
            encode_data['scope'] = token_data.permission_level
        else:
            raise IncorrectTokenDataException(f"insufficient data provided for specified token type "
                                              f"({token_data.token_type}) requires specifying user's permissions")
    else:
        if token_data.permission_level:
            raise IncorrectTokenDataException(f"specified user's permission but token type is {token_data.token_type} "
                                              f"did you mean to create an access or refresh token instead?")

    match token_data.token_type:
        case TokenType.email_verification_token:
            expire_minutes = settings.MAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
        case TokenType.password_reset_token:
            expire_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        case TokenType.access_token:
            expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        case TokenType.refresh_token:
            expire_minutes = None
        case _:
            raise ValueError('token_type must be a valid enumeration member of TokenType enum')

    now = datetime.utcnow()
    encode_data['iat'] = now

    if token_data.token_type != TokenType.refresh_token:
        expires = now + timedelta(minutes=expire_minutes)
        encode_data['exp'] = expires

    access_token = jwt.encode(encode_data, settings.API_SECRET, algorithm=settings.ALGORITHM)

    return access_token


def decode_jwt(token: str, *, expected_token_type: TokenType, on_error: Optional[Callable] = None, **kwargs):
    try:
        payload = jwt.decode(token, settings.API_SECRET, algorithms=[settings.ALGORITHM])
    except JWTError:
        if on_error:
            on_error(**kwargs)
        if expected_token_type == TokenType.access_token:
            raise InvalidTokenException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail='Could not validate credentials',
                                        headers={"WWW-Authenticate": "Bearer"})
        elif expected_token_type == TokenType.refresh_token:
            raise InvalidTokenException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail='Invalid refresh token provided')
        else:
            raise InvalidTokenException()

    token_type = payload.get('type')

    if token_type != expected_token_type:
        raise IncorrectTokenDataException('Token types mismatch')

    user_id = payload.get("sub")
    permissions_level: str = payload.get('scope')

    match token_type:
        case TokenType.access_token, TokenType.refresh_token:
            token_data = ReturnAccessTokenPayload(user_id=user_id,
                                                  permission_level=permissions_level,
                                                  access_token=token)
        case _:
            token_data = ReturnGenericToken(user_id=user_id)

    return token_data


def get_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_jwt(token, expected_token_type=TokenType.access_token)
    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    session_db = db.query(models.Session).where(models.Session.user_id == user.id
                                                and models.Session.access_token == token).first()

    if not session_db:
        raise SessionNotFoundHTTPException()

    if user.disabled:
        raise AccountDisabledHTTPException()

    return user


def get_verified_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_jwt(token, expected_token_type=TokenType.access_token)
    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    session_db = db.query(models.Session).where(models.Session.user_id == user.id
                                                and models.Session.access_token == token).first()

    if not session_db:
        raise SessionNotFoundHTTPException()

    if user.disabled:
        raise AccountDisabledHTTPException()

    if not user.verified:
        raise UnverifiedUserHTTPException()

    return user


def get_administrative_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_jwt(token, expected_token_type=TokenType.access_token)
    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    session_db = db.query(models.Session).where(models.Session.user_id == user.id
                                                and models.Session.access_token == token).first()

    if not session_db:
        raise SessionNotFoundHTTPException()

    if user.disabled:
        raise AccountDisabledHTTPException()

    if not user.verified:
        raise UnverifiedUserHTTPException()

    user_permissions = user.permission_level.split(' ')

    if 'admin' not in user_permissions:
        raise InsufficientPermissionHTTPException()

    return user
