from datetime import datetime, timedelta
from typing import List, Union

from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException, Header
from ..config import settings
from sqlalchemy.orm import Session
from ..database import get_db
from ..exceptions import CooldownHTTPException, InvalidTokenException, MalformedAccessTokenException, \
    InvalidEnumerationMemberHTTPException
from ..schemas.oauth2 import TokenType
from ..schemas.user import CreateUser, ReturnUser, ReturnUserAndSettings, ReturnUserDetailed, ReturnUsers, \
    UserEmailOnly
from ..schemas.user_settings import AvailableContentLanugages, AvailableSettings, AvailableThemes, PreferredThemeBase, \
    LanguageCreate, ReturnSetting
from ..schemas.email_request import EmailRequestType, EmailVerificationRequest
from .. import models
from ..email_manager import create_email_verification_email, create_email_request, send_email
from sqlalchemy.exc import IntegrityError
from pydantic import Required, UUID4
from .. import utils, oauth2
from ..utils import on_decode_error

router = APIRouter(prefix=settings.BASE_URL + '/users',
                   tags=['Users'])


@router.post('/register', status_code=status.HTTP_201_CREATED, response_model=ReturnUserAndSettings)
def create_user(user: CreateUser,
                background_tasks: BackgroundTasks,
                db: Session = Depends(get_db),
                content_language: AvailableContentLanugages = Header(Required),
                preferred_theme: AvailableThemes = Header(Required)) -> dict[str, Union[ReturnUser,
                                                                                        List[ReturnSetting]]]:
    """
    ## Part of the user creation process is initializing the user's settings
    ### For this reason it is required to pass two *header parameters*: `content-language` and `preferred-theme` to this endpoint
    ### Later on these settings can be accessed and modified via *`/api/settings/`* endpoint

    #### `content-language` is a **required** *header parameter* used to represent user's preferred content language.

    It can only be set to one of the following two values as these are the only languages currently supported
    both by this API and [Zołza Hairstyles](https://mephew.ddns.net) website :
    - **pl** for Polish content
    - **en** for English content

    This value will be saved in the database as the user's language in the created user's settings.

    This particular endpoint uses this value to determine the apropriate language of the account activation message
    sent to the user after the account is created.

    Other endpoints use this value in a similiar manner (e.g. when sending messages related to 2FA setup, user
    permissions updates or upcoming appointments notices)


    #### `preferred-theme` is a **required** *header parameter* used to represent user's preferred application theme

    It can only be set to one of the following two values as these are the only themes currently supported
    by [Zołza Hairstyles](https://mephew.ddns.net) website :
    - **dark** for dark theme
    - **light** for light theme

    This value will be saved in the database as the user's preferred theme in the created user's settings.

    This particular endpoint uses this value only for the sole purpose of user config initialization in order to
    provide consistent theming experience across multiple devices and/or web browsers
    """

    user_theme = PreferredThemeBase(current_value=preferred_theme)

    if content_language == content_language.polish:
        user_language = LanguageCreate(current_value=AvailableContentLanugages.polish)
    elif content_language == content_language.english:
        user_language = LanguageCreate(current_value=AvailableContentLanugages.english)
    else:
        raise InvalidEnumerationMemberHTTPException

    new_user = user.dict()

    new_user['hashed_password'] = utils.hash_password(new_user.pop('password'))

    new_user = models.User(**new_user)
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f'user with an email address of {user.email} already exists')

    db.refresh(new_user)

    user_theme = user_theme.dict()
    user_theme['user_id'] = new_user.id
    user_theme_db = models.Setting(**user_theme)
    db.add(user_theme_db)

    user_language = user_language.dict()
    user_language['user_id'] = new_user.id
    user_language_db = models.Setting(**user_language)
    db.add(user_language_db)

    db.commit()

    user_settings = db.query(models.Setting).filter(models.Setting.user_id == new_user.id).all()

    email_verification_request = create_email_request(user=new_user,
                                                      token_type=TokenType.email_verification_token,
                                                      request_type=EmailRequestType.email_verification_request)

    db.add(email_verification_request)

    message, template_name = create_email_verification_email(content_language,
                                                             new_user,
                                                             email_verification_request.request_token)

    background_tasks.add_task(send_email, message, template_name)

    return {'user': new_user,
            'settings': user_settings}


@router.post('/request-email-verification',
             status_code=status.HTTP_202_ACCEPTED,
             response_model=UserEmailOnly)
def request_email_verification(user_email: UserEmailOnly,
                               background_tasks: BackgroundTasks,
                               db: Session = Depends(get_db)) -> UserEmailOnly:
    user_db = db.query(models.User).where(models.User.email == user_email.email).first()

    if not user_db:
        raise HTTPException(detail=f'user with an email address of {user_email.email} was not found',
                            status_code=status.HTTP_404_NOT_FOUND)

    db_email_verification_request = db.query(models.EmailRequests) \
        .where(models.EmailRequests.user_id == user_db.id
               and models.EmailRequests.request_type == EmailRequestType.email_verification_request).first()

    if db_email_verification_request:
        cooldown_start = db_email_verification_request.created_at
        cooldown_end = cooldown_start + timedelta(minutes=settings.MAIL_VERIFICATION_COOLDOWN_MINUTES)
        now = datetime.now().astimezone()

        if cooldown_end > now:
            # noinspection PyTypeChecker
            raise CooldownHTTPException(cooldown_end - now, detail=f'Too many '
                                                                   f'verification requests, max 1 request per'
                                                                   f' {settings.MAIL_VERIFICATION_COOLDOWN_MINUTES}'
                                                                   f' minutes allowed')

        db.delete(db_email_verification_request)

    email_verification_request = create_email_request(user=user_db,
                                                      token_type=TokenType.email_verification_token,
                                                      request_type=EmailRequestType.email_verification_request)

    db.add(email_verification_request)
    db.commit()

    content_language = db.query(models.Setting).where(models.Setting.name == AvailableSettings.language
                                                      and models.Setting.user_id == user_db.id).first()

    message, template_name = create_email_verification_email(content_language.current_value,
                                                             user_db,
                                                             email_verification_request.request_token)

    background_tasks.add_task(send_email, message, template_name)

    return user_email


@router.put('/email-verification', response_model=ReturnUser)
def verify_email(email_verification_request: EmailVerificationRequest,
                 db: Session = Depends(get_db)) -> ReturnUser:

    request_db = db.query(models.EmailRequests) \
        .where(models.EmailRequests.request_type == EmailRequestType.email_verification_request
               and models.EmailRequests.request_token == email_verification_request.verification_token).first()

    if not request_db:
        raise HTTPException(detail='Invalid verification token provided',
                            status_code=status.HTTP_401_UNAUTHORIZED)

    token_db = request_db.request_token

    if not token_db:
        raise HTTPException(detail='Invalid verification token provided',
                            status_code=status.HTTP_401_UNAUTHORIZED)

    payload = oauth2.decode_jwt(email_verification_request.verification_token,
                                expected_token_type=TokenType.email_verification_token,
                                on_error=on_decode_error, db=db, request_db=request_db)

    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    user.verified = True
    db.commit()
    db.refresh(user)

    return user


@router.get('/me', response_model=ReturnUser, name='Get info about your account')
async def me(db: Session = Depends(get_db),
             user=Depends(oauth2.get_user)) -> ReturnUser:
    user_id = user.id
    user = db.query(models.User).where(models.User.id == user_id).first()

    return user


@router.get('', response_model=ReturnUsers)
def get_users(db: Session = Depends(get_db),
              _=Depends(oauth2.get_administrative_user)) -> dict[str, ReturnUser]:
    users_db = db.query(models.User).all()

    return {'users': users_db}


@router.get('/user/{uuid}', response_model=ReturnUserDetailed)
def get_user_by_uuid(uuid: UUID4,
                     db: Session = Depends(get_db),
                     _=Depends(oauth2.get_administrative_user)) -> ReturnUserDetailed:
    user_db = db.query(models.User).where(models.User.id == uuid).first()

    if not user_db:
        raise HTTPException(detail=f'User with uuid of {uuid} does not exist',
                            status_code=status.HTTP_404_NOT_FOUND)

    return user_db


@router.put('/ban/{uuid}')
def block_user(uuid: UUID4,
               db: Session = Depends(get_db),
               _=Depends(oauth2.get_administrative_user)):
    raise NotImplementedError


@router.put('/promote/{uuid}')
def promote_user(uuid: UUID4,
                 db: Session = Depends(get_db),
                 _=Depends(oauth2.get_administrative_user)):
    raise NotImplementedError


@router.put('/demote/{uuid}')
def demote_user(uuid: UUID4,
                db: Session = Depends(get_db),
                _=Depends(oauth2.get_administrative_user)):
    raise NotImplementedError
