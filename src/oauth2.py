from jose import JWTError, jwt
from datetime import datetime, timedelta

from . import models
from .config import settings
from typing import Optional, Callable
from fastapi import Depends, Header, status, Request
from sqlalchemy.orm import Session
from .database import get_db
from fastapi.security import OAuth2PasswordBearer
from .schemas.oauth2 import (
    TokenPayloadBase,
    ReturnAccessTokenPayload,
    ReturnGenericToken,
    TokenType,
    UserSession,
    VerifiedUserSession,
    AdminSession,
    SuperuserSession,
)
from .exceptions import (
    AccountDisabledHTTPException,
    AdditionalAuthenticationRequiredHTTPException,
    IncorrectTokenDataException,
    InsufficientPermissionsHTTPException,
    InvalidTokenHTTPException,
    SessionNotFoundHTTPException,
    UnverifiedUserHTTPException, UserNotFoundException,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_jwt(token_data: TokenPayloadBase):
    encode_data = {"sub": str(token_data.user_id), "type": token_data.token_type}

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
            raise ValueError(
                "token_type must be a valid enumeration member of TokenType enum"
            )

    now = datetime.utcnow()
    encode_data["iat"] = now

    if token_data.token_type != TokenType.refresh_token:
        expires = now + timedelta(minutes=expire_minutes)
        encode_data["exp"] = expires

    access_token = jwt.encode(
        encode_data, settings.API_SECRET, algorithm=settings.ALGORITHM
    )

    return access_token


def decode_jwt(
    token: str,
    *,
    expected_token_type: TokenType,
    on_error: Optional[Callable] = None,
    **kwargs
):
    try:
        payload = jwt.decode(
            token, settings.API_SECRET, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        if on_error:
            on_error(**kwargs)
        if expected_token_type == TokenType.access_token:
            raise InvalidTokenHTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif expected_token_type == TokenType.refresh_token:
            raise InvalidTokenHTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token provided",
            )
        else:
            raise InvalidTokenHTTPException()

    token_type = payload.get("type")

    if token_type != expected_token_type:
        raise IncorrectTokenDataException("Token types mismatch")

    user_id = payload.get("sub")

    match token_type:
        case TokenType.access_token, TokenType.refresh_token:
            token_data = ReturnAccessTokenPayload(user_id=user_id, access_token=token)
        case _:
            token_data = ReturnGenericToken(user_id=user_id)

    return token_data


def get_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    user_agent: str | None = Header(None),
) -> UserSession:
    payload = decode_jwt(token, expected_token_type=TokenType.access_token)
    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    if not user:
        raise UserNotFoundException()

    session_db = (
        db.query(models.Session)
        .where(
            models.Session.user_id == user.id and models.Session.access_token == token
        )
        .first()
    )

    if not session_db:
        raise SessionNotFoundHTTPException()

    session_db.last_accessed = datetime.now().astimezone()
    session_db.last_user_agent = user_agent
    session_db.last_ip_address = request.client.host

    if user.disabled:
        raise AccountDisabledHTTPException()

    user_session = UserSession(user=user, session=session_db)

    return user_session


def get_verified_user(user_session=Depends(get_user)) -> VerifiedUserSession:
    user = user_session.user

    if not user.verified:
        raise UnverifiedUserHTTPException()

    verified_user_session = VerifiedUserSession(
        **user_session.dict(), verified_user=user_session.user
    )

    return verified_user_session


def get_admin(verified_user_session=Depends(get_verified_user)) -> AdminSession:
    verified_user = verified_user_session.verified_user

    if "admin" not in verified_user.permission_level:
        raise InsufficientPermissionsHTTPException()

    admin_session = AdminSession(**verified_user_session.dict(), admin=verified_user)

    return admin_session


def get_superuser(admin_session=Depends(get_admin)) -> SuperuserSession:
    admin = admin_session.admin

    if "superuser" not in admin.permission_level:
        raise InsufficientPermissionsHTTPException()

    superuser_session = SuperuserSession(**admin_session.dict(), superuser=admin)

    return superuser_session


def ensure_sudo(session):
    if not session.sudo_mode_activated:
        raise AdditionalAuthenticationRequiredHTTPException()

    if not session.sudo_mode_expires > datetime.now().astimezone():
        raise AdditionalAuthenticationRequiredHTTPException()


def get_user_sudo(user_session=Depends(get_user)) -> UserSession:
    ensure_sudo(user_session.session)

    return user_session


def get_verified_user_sudo(
    verified_user_session=Depends(get_verified_user),
) -> VerifiedUserSession:
    ensure_sudo(verified_user_session.session)

    return verified_user_session


def get_admin_sudo(admin_session=Depends(get_admin)) -> AdminSession:
    ensure_sudo(admin_session.session)

    return admin_session


def get_superuser_sudo(superuser_session=Depends(get_superuser)) -> SuperuserSession:
    ensure_sudo(superuser_session.session)

    return superuser_session
