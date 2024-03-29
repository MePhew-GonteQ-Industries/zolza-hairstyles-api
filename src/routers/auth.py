from datetime import datetime, timedelta
from typing import Annotated, List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Header,
    Request,
    status,
)
from fastapi.security.oauth2 import OAuth2PasswordRequestFormStrict
from fastapi_mail import FastMail
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models, oauth2, utils
from ..config import settings
from ..database import get_db
from ..email_manager import (
    create_email_request,
    create_password_reset_email,
    get_fast_mail_client,
    send_email,
)
from ..exceptions import (
    CooldownHTTPException,
    InvalidGrantTypeHTTPException,
    ResourceNotFoundHTTPException,
    SessionNotFoundHTTPException,
)
from ..loggers import app_logger
from ..schemas import session
from ..schemas.email_request import EmailRequestType, PasswordResetRequest
from ..schemas.oauth2 import (
    PasswordChangeForm,
    ReturnAccessToken,
    SudoModeInfo,
    TokenPayloadBase,
    TokenType,
)
from ..schemas.session import (
    ReturnActiveSession,
)
from ..schemas.user import UserEmailOnly
from ..schemas.user_settings import AvailableSettings
from ..utils import (
    load_session_data,
    on_decode_error,
    verify_password,
)

router = APIRouter(prefix=settings.BASE_URL + "/auth", tags=["Authorization"])


@router.post("/login", response_model=ReturnAccessToken)
def login(
    request: Request,
    user_credentials: OAuth2PasswordRequestFormStrict = Depends(),
    db: Session = Depends(get_db),
    user_agent: str | None = Header(None),
):
    if user_credentials.grant_type != "password":
        raise InvalidGrantTypeHTTPException("password")

    user = (
        db.query(models.User)
        .filter(models.User.email == user_credentials.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid credentials"
        )

    verify_password(password=user_credentials.password, user_id=user.id, db=db)

    token_data = TokenPayloadBase(user_id=user.id, token_type=TokenType.access_token)

    access_token = oauth2.create_jwt(token_data)

    token_data.token_type = TokenType.refresh_token

    refresh_token = oauth2.create_jwt(token_data)

    user_ip_address = request.client.host

    db_session = models.Session(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        sign_in_user_agent=user_agent,
        last_user_agent=user_agent,
        sign_in_ip_address=user_ip_address,
        last_ip_address=user_ip_address,
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    user_session = session.ActiveUserSession(
        id=db_session.id,
        first_accessed=db_session.first_accessed,
        last_accessed=db_session.last_accessed,
        sign_in_user_agent=db_session.sign_in_user_agent,
        sign_in_ip_address=db_session.sign_in_ip_address,
        last_user_agent=db_session.last_user_agent,
        last_ip_address=db_session.last_ip_address,
        user=user,
    )

    return ReturnAccessToken(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        session=user_session,
    )


@router.post("/refresh-token", response_model=ReturnAccessToken, name="Refresh Token")
def token_refresh(
    request: Request,
    refresh_token: Annotated[str, Form()],
    grant_type: Annotated[str, Form()],
    db: Session = Depends(get_db),
    user_agent: str | None = Header(None),
):
    if grant_type != "refresh_token":
        raise InvalidGrantTypeHTTPException("refresh_token")

    payload = oauth2.decode_jwt(
        refresh_token, expected_token_type=TokenType.refresh_token
    )

    db_session = (
        db.query(models.Session)
        .where(models.Session.user_id == payload.user_id)
        .where(models.Session.refresh_token == refresh_token)
        .first()
    )

    if not db_session:
        raise SessionNotFoundHTTPException()

    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    token_data = TokenPayloadBase(user_id=user.id, token_type=TokenType.access_token)

    access_token = oauth2.create_jwt(token_data)

    token_data.token_type = TokenType.refresh_token

    refresh_token = oauth2.create_jwt(token_data)

    db_session.access_token = access_token
    db_session.refresh_token = refresh_token
    db_session.last_accessed = datetime.utcnow()
    db_session.last_user_agent = user_agent
    db_session.last_ip_address = request.client.host

    db.commit()
    db.refresh(db_session)

    user_session = session.ActiveUserSession(
        id=db_session.id,
        first_accessed=db_session.first_accessed,
        last_accessed=db_session.last_accessed,
        sign_in_user_agent=db_session.sign_in_user_agent,
        sign_in_ip_address=db_session.sign_in_ip_address,
        last_user_agent=db_session.last_user_agent,
        last_ip_address=db_session.last_ip_address,
        user=user,
    )

    return ReturnAccessToken(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        session=user_session,
    )


@router.post("/logout")
def logout(
    db: Session = Depends(get_db), user_session=Depends(oauth2.get_user_no_verification)
):
    session_query = (
        db.query(models.Session)
        .where(models.Session.user_id == user_session.user.id)
        .where(models.Session.access_token == user_session.session.access_token)
    )

    session_db = session_query.first()

    db.query(models.FcmToken).where(
        models.FcmToken.session_id == session_db.id
    ).delete()

    session_query.delete()

    db.commit()

    return {"status": "ok"}


@router.post("/logout-everywhere")
def logout_everywhere(
    db: Session = Depends(get_db), user_session=Depends(oauth2.get_user)
):
    db.query(models.Session).where(
        models.Session.user_id == user_session.user.id
    ).where(models.Session.id != user_session.session.id).delete()

    db.commit()

    return {"status": "ok"}


@router.post(
    "/request-password-reset",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset(
    user_email: UserEmailOnly,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    fast_mail_client: FastMail = Depends(get_fast_mail_client),
):
    app_logger.info(f"Received password reset request for email {user_email}")
    user_db = db.query(models.User).where(models.User.email == user_email.email).first()

    if not user_db:
        app_logger.info(f"Could not find user with an email of {user_email}")
        return user_email

    app_logger.info(
        f"User with an email of {user_email} "
        f"was found: {user_db.name} {user_db.surname}"
    )

    db_password_reset_request = (
        db.query(models.EmailRequests)
        .where(models.EmailRequests.user_id == user_db.id)
        .where(
            models.EmailRequests.request_type == EmailRequestType.password_reset_request
        )
        .first()
    )

    app_logger.info(
        f"Found existing password reset request for this user " f"({user_email})"
    )

    if db_password_reset_request:
        cooldown_start = db_password_reset_request.created_at
        cooldown_end = cooldown_start + timedelta(
            minutes=settings.PASSWORD_RESET_COOLDOWN_MINUTES
        )
        now = datetime.utcnow()
        # noinspection PyTypeChecker,PydanticTypeChecker
        cooldown_left = cooldown_end - now

        if cooldown_end > now:
            # noinspection PyTypeChecker,PydanticTypeChecker
            app_logger.info(
                f"Password reset request cooldown is still in effect "
                f"for this user ({user_email}), not sending another one"
            )
            raise CooldownHTTPException(
                str(int(cooldown_left.total_seconds())),
                detail=f"Too many password reset requests, max 1 request per "
                f"{settings.PASSWORD_RESET_COOLDOWN_MINUTES} minutes allowed",
            )
        app_logger.info(
            f"Password reset request cooldown is not in effect anymore "
            f"for this user ({user_email}), creating another one"
        )
        db.delete(db_password_reset_request)

    password_reset_request = create_email_request(
        user=user_db,
        token_type=TokenType.password_reset_token,
        request_type=EmailRequestType.password_reset_request,
    )

    db.add(password_reset_request)
    db.commit()

    app_logger.info(f"Successfully created new password reset request for {user_email}")

    content_language = (
        db.query(models.Setting)
        .where(models.Setting.name == AvailableSettings.language)
        .where(models.Setting.user_id == user_db.id)
        .first()
    )

    message, template_name = create_password_reset_email(
        content_language.current_value, user_db, password_reset_request.request_token
    )

    background_tasks.add_task(send_email, message, template_name, fast_mail_client)

    app_logger.info(
        f"Successfully added password reset request task for user " f"{user_db.email}"
    )

    return {"status": "ok"}


@router.put("/reset-password")
def reset_password(
    password_reset_request: PasswordResetRequest, db: Session = Depends(get_db)
):
    request_db = (
        db.query(models.EmailRequests)
        .where(
            models.EmailRequests.request_type == EmailRequestType.password_reset_request
        )
        .where(models.EmailRequests.request_token == password_reset_request.reset_token)
        .first()
    )

    if not request_db:
        raise HTTPException(
            detail="invalid reset code provided",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token_db = request_db.request_token

    if not token_db:
        raise HTTPException(
            detail="invalid reset code provided",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    payload = oauth2.decode_jwt(
        password_reset_request.reset_token,
        expected_token_type=TokenType.password_reset_token,
        on_error=on_decode_error,
        db=db,
        request_db=request_db,
    )

    utils.change_password(
        new_password=password_reset_request.new_password, user_id=payload.user_id, db=db
    )

    return {"status": "ok"}


@router.post("/change-password")
def change_password(
    password_change_form: PasswordChangeForm,
    db: Session = Depends(get_db),
    user_session=Depends(oauth2.get_user),
):
    user = user_session.user

    verify_password(password=password_change_form.old_password, user_id=user.id, db=db)
    utils.change_password(
        new_password=password_change_form.new_password, user_id=user.id, db=db
    )

    return {"status": "ok"}


@router.post("/enter-sudo-mode", response_model=SudoModeInfo)
def enter_sudo_mode(
    password: Annotated[str, Form()],
    db: Session = Depends(get_db),
    user_session=Depends(oauth2.get_user),
):
    verify_password(password=password, user_id=user_session.user.id, db=db)

    sudo_mode_start = datetime.utcnow()

    user_session.session.sudo_mode_activated = sudo_mode_start

    user_session.session.sudo_mode_expires = sudo_mode_start + timedelta(
        hours=settings.SUDO_MODE_TIME_HOURS
    )

    db.commit()

    db.refresh(user_session.session)

    sudo_mode_info = SudoModeInfo(
        sudo_mode_activated=user_session.session.sudo_mode_activated,
        sudo_mode_expires=user_session.session.sudo_mode_expires,
    )

    return sudo_mode_info


@router.get("/sessions", response_model=List[ReturnActiveSession])
def get_sessions(db: Session = Depends(get_db), user_session=Depends(oauth2.get_user)):
    user = user_session.user

    sessions = (
        db.query(models.Session)
        .where(models.Session.user_id == user.id)
        .order_by(models.Session.last_accessed.desc())
        .all()
    )

    sessions_with_data = []

    for session_db in sessions:
        session_with_data = load_session_data(session_db)
        sessions_with_data.append(session_with_data)

    return sessions_with_data


@router.get("/sessions/{session_id}", response_model=ReturnActiveSession)
def get_session(
    session_id: UUID4,
    db: Session = Depends(get_db),
    user_session=Depends(oauth2.get_user),
):
    user = user_session.user

    session_db = (
        db.query(models.Session)
        .where(models.Session.user_id == user.id)
        .where(models.Session.id == session_id)
        .first()
    )

    if not session_db:
        raise ResourceNotFoundHTTPException

    session_db = load_session_data(session_db)

    return session_db


@router.delete("/revoke-session/{session_id}")
def revoke_session(
    session_id: UUID4,
    db: Session = Depends(get_db),
    user_session=Depends(oauth2.get_user),
):
    user = user_session.user
    session_db = (
        db.query(models.Session)
        .where(models.Session.user_id == user.id)
        .where(models.Session.id == session_id)
        .first()
    )

    if not session_db:
        raise ResourceNotFoundHTTPException

    db.delete(session_db)
    db.commit()

    return {"status": "ok"}


@router.post("/enable-two-factor-authentication")
def enable_two_factor_authentication():
    raise NotImplementedError


@router.post("/disable-two-factor-authentication")
def disable_two_factor_authentication():
    raise NotImplementedError
