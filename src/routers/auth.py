from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Form, BackgroundTasks
from pydantic import Required
from fastapi.security.oauth2 import OAuth2PasswordRequestFormStrict
from sqlalchemy.orm import Session

from ..email_manager import create_email_request, create_password_reset_email, send_email
from ..exceptions import CooldownHTTPException, InvalidGrantTypeException, SessionNotFoundHTTPException
from ..schemas.email_request import EmailRequestType, PasswordResetRequest
from ..schemas.oauth2 import ReturnAccessToken
from ..schemas.oauth2 import CreateTokenPayload, TokenType
from ..schemas import session

from .. import models, utils, oauth2
from ..config import settings
from ..database import get_db
from ..schemas.user import UserEmailOnly
from ..schemas.user_settings import AvailableSettings
from ..utils import on_decode_error

router = APIRouter(prefix=settings.BASE_URL + '/auth',
                   tags=['Authorization'])


@router.post('/login', response_model=ReturnAccessToken)
def login(user_credentials: OAuth2PasswordRequestFormStrict = Depends(), db: Session = Depends(get_db)):
    if user_credentials.grant_type != 'password':
        raise InvalidGrantTypeException('password')

    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='invalid credentials')

    password_hash = db.query(models.Password.password_hash).where(models.Password.user_id == user.id) \
        .where(models.Password.current == True).first()

    if not utils.compare_passwords(user_credentials.password, *password_hash):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='invalid credentials')

    user_permissions = ' '.join(map(str, user.permission_level))

    token_data = CreateTokenPayload(user_id=user.id,
                                    permission_level=user_permissions,
                                    token_type=TokenType.access_token)

    access_token = oauth2.create_jwt(token_data)

    token_data.token_type = TokenType.refresh_token

    refresh_token = oauth2.create_jwt(token_data)

    new_session = session.Session(user_id=user.id,
                                  access_token=access_token,
                                  refresh_token=refresh_token)

    db_session = models.Session(**new_session.dict())

    db.add(db_session)

    db.commit()

    return ReturnAccessToken(access_token=access_token,
                             token_type='bearer',
                             scope=user_permissions,
                             expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                             refresh_token=refresh_token)


@router.post('/refresh-token', response_model=ReturnAccessToken, name='Refresh Token')
def token_refresh(db: Session = Depends(get_db),
                  refresh_token: str = Form(Required),
                  grant_type: str = Form(Required)):
    if grant_type != 'refresh_token':
        raise InvalidGrantTypeException('refresh_token')

    payload = oauth2.decode_jwt(refresh_token, expected_token_type=TokenType.refresh_token)

    db_session = db.query(models.Session).where(models.Session.user_id == payload.user_id
                                                and models.Session.refresh_token == refresh_token).first()

    if not db_session:
        raise SessionNotFoundHTTPException()

    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    db.delete(db_session)
    db.commit()

    user_permissions = ' '.join(map(str, user.permission_level))

    token_data = CreateTokenPayload(user_id=user.id,
                                    permission_level=user_permissions,
                                    token_type=TokenType.access_token)

    access_token = oauth2.create_jwt(token_data)

    token_data.token_type = TokenType.refresh_token

    refresh_token = oauth2.create_jwt(token_data)

    new_session = session.Session(user_id=user.id,
                                  access_token=access_token,
                                  refresh_token=refresh_token)

    db_session = models.Session(**new_session.dict())

    db.add(db_session)

    db.commit()

    return ReturnAccessToken(access_token=access_token,
                             token_type='bearer',
                             scope=user_permissions,
                             expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                             refresh_token=refresh_token)


@router.post('/logout')
def logout(db: Session = Depends(get_db),
           user=Depends(oauth2.get_user)):
    session_db = db.query(models.Session).where(models.Session.user_id == user.id
                                                and models.Session.access_token == user.access_token).first()
    db.delete(session_db)
    db.commit()

    return {'status': 'ok'}


@router.post('/logout-everywhere')
def logout_everywhere(db: Session = Depends(get_db),
                      user=Depends(oauth2.get_user)):
    query = models.Session.__table__.delete().where(models.Session.user_id == user.id)
    db.execute(query)
    db.commit()

    return {'status': 'ok'}


@router.post('/request-password-reset',
             status_code=status.HTTP_202_ACCEPTED,
             response_model=UserEmailOnly)
def request_password_reset(user_email: UserEmailOnly,
                           background_tasks: BackgroundTasks,
                           db: Session = Depends(get_db)):
    user_db = db.query(models.User).where(models.User.email == user_email.email).first()

    if not user_db:
        return user_email

    db_password_reset_request = db.query(models.EmailRequests).where(models.EmailRequests.user_id == user_db.id
                                                                     and models.EmailRequests.request_type ==
                                                                     EmailRequestType.password_reset_request).first()

    if db_password_reset_request:
        cooldown_start = db_password_reset_request.created_at
        cooldown_end = cooldown_start + timedelta(minutes=settings.PASSWORD_RESET_COOLDOWN_MINUTES)
        now = datetime.now().astimezone()
        # noinspection PyTypeChecker,PydanticTypeChecker
        cooldown_left = cooldown_end - now

        if cooldown_end > now:
            # noinspection PyTypeChecker,PydanticTypeChecker
            raise CooldownHTTPException(str(int(cooldown_left.total_seconds())),
                                        detail=f'Too many password reset requests, max 1 request per '
                                               f'{settings.PASSWORD_RESET_COOLDOWN_MINUTES} minutes allowed')
        db.delete(db_password_reset_request)

    password_reset_request = create_email_request(user=user_db,
                                                  token_type=TokenType.password_reset_token,
                                                  request_type=EmailRequestType.password_reset_request)

    db.add(password_reset_request)
    db.commit()

    content_language = db.query(models.Setting).where(models.Setting.name == AvailableSettings.language
                                                      and models.Setting.user_id == user_db.id).first()

    message, template_name = create_password_reset_email(content_language.current_value,
                                                         user_db,
                                                         password_reset_request.request_token)

    background_tasks.add_task(send_email, message, template_name)

    return user_email


@router.put('/reset-password')
def reset_password(password_reset_request: PasswordResetRequest, db: Session = Depends(get_db)):
    request_db = db.query(models.EmailRequests) \
        .where(models.EmailRequests.request_type == EmailRequestType.password_reset_request
               and models.EmailRequests.request_token == password_reset_request.reset_token).first()

    if not request_db:
        raise HTTPException(detail='invalid reset code provided',
                            status_code=status.HTTP_401_UNAUTHORIZED)

    token_db = request_db.request_token

    if not token_db:
        raise HTTPException(detail='invalid reset code provided',
                            status_code=status.HTTP_401_UNAUTHORIZED)

    payload = oauth2.decode_jwt(password_reset_request.reset_token,
                                expected_token_type=TokenType.password_reset_token,
                                on_error=on_decode_error, db=db, request_db=request_db)

    recent_passwords = db.query(models.Password).where(models.Password.user_id == payload.user_id).all()

    for recent_password in recent_passwords:
        if utils.compare_passwords(password_reset_request.new_password,
                                   recent_password.password_hash):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail='new password cannot be the same as any of the last 5 passwords used by the '
                                       'user')

    old_passwords = db.query(models.Password).where(models.Password.user_id == payload.user_id) \
        .where(models.Password.current == False).order_by(models.Password.created_at.desc()).offset(4).all()

    for old_password in old_passwords:
        db.delete(old_password)

    db.commit()

    current_password = db.query(models.Password).where(models.Password.user_id == payload.user_id) \
        .where(models.Password.current).first()

    current_password.current = False

    db.commit()

    new_password = models.Password(password_hash=utils.hash_password(password_reset_request.new_password),
                                   user_id=payload.user_id,
                                   current=True)

    db.add(new_password)

    db.commit()

    return {'status': 'ok'}


@router.post('/enable-two-factor-authentication')
def enable_two_factor_authentication():
    raise NotImplementedError


@router.post('/disable-two-factor-authentication')
def disable_two_factor_authentication():
    raise NotImplementedError
