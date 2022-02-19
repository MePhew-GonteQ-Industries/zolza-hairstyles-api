from datetime import datetime, timedelta
from typing import List, Union

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Header,
    status,
)
from fastapi.security import OAuth2PasswordRequestFormStrict
from pydantic import Required, UUID4
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, oauth2, utils
from ..config import settings
from ..database import get_db
from ..email_manager import (
    create_email_request,
    create_email_verification_email,
    send_email,
)
from ..exceptions import (
    CooldownHTTPException,
    InvalidEnumerationMemberHTTPException,
    InvalidGrantTypeException,
)
from ..schemas.email_request import EmailRequestType, EmailVerificationRequest
from ..schemas.oauth2 import TokenType
from ..schemas.user import (
    CreateUser,
    Gender,
    ReturnUser,
    ReturnUserAndSettings,
    ReturnUserDetailed,
    ReturnUsers,
    UserEmailOnly,
)
from ..schemas.user_settings import (
    AvailableContentLanguages,
    AvailableSettings,
    AvailableThemes,
    LanguageCreate,
    PreferredThemeBase,
    ReturnSetting,
)
from ..utils import get_user_from_db, on_decode_error

router = APIRouter(prefix=settings.BASE_URL + "/users", tags=["Users"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ReturnUserAndSettings,
)
def create_user(
    user: CreateUser,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    content_language: AvailableContentLanguages = Header(Required),
    preferred_theme: AvailableThemes = Header(Required),
) -> dict[str, Union[ReturnUser, List[ReturnSetting]]]:
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

    This particular endpoint uses this value to determine the appropriate language of the account activation message
    sent to the user after the account is created.

    Other endpoints use this value in a similar manner (e.g. when sending messages related to 2FA setup, user
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
        user_language = LanguageCreate(current_value=AvailableContentLanguages.polish)
    elif content_language == content_language.english:
        user_language = LanguageCreate(current_value=AvailableContentLanguages.english)
    else:
        raise InvalidEnumerationMemberHTTPException

    new_user = user.dict()

    hashed_password = utils.hash_password(new_user.pop("password"))

    new_user = models.User(**new_user)
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with an email address of {user.email} already exists",
        )

    db.refresh(new_user)

    password = models.Password(
        password_hash=hashed_password, user_id=new_user.id, current=True
    )
    db.add(password)
    db.commit()

    user_theme = user_theme.dict()
    user_theme["user_id"] = new_user.id
    user_theme_db = models.Setting(**user_theme)
    db.add(user_theme_db)

    user_language = user_language.dict()
    user_language["user_id"] = new_user.id
    user_language_db = models.Setting(**user_language)
    db.add(user_language_db)

    db.commit()

    user_settings = (
        db.query(models.Setting).filter(models.Setting.user_id == new_user.id).all()
    )

    new_user.settings = user_settings

    email_verification_request = create_email_request(
        user=new_user,
        token_type=TokenType.email_verification_token,
        request_type=EmailRequestType.email_verification_request,
    )

    db.add(email_verification_request)

    message, template_name = create_email_verification_email(
        content_language, new_user, email_verification_request.request_token
    )

    background_tasks.add_task(send_email, message, template_name)

    return new_user


# todo: fastapi limiter: 1 per 5 minutes
@router.post(
    "/request-email-verification",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=UserEmailOnly,
)
def request_email_verification(
    user_email: UserEmailOnly,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> UserEmailOnly:
    user_db = db.query(models.User).where(models.User.email == user_email.email).first()

    if not user_db:
        return user_email

    db_email_verification_request = (
        db.query(models.EmailRequests)
        .where(
            models.EmailRequests.user_id == user_db.id
            and models.EmailRequests.request_type
            == EmailRequestType.email_verification_request
        )
        .first()
    )

    if db_email_verification_request:
        cooldown_start = db_email_verification_request.created_at
        cooldown_end = cooldown_start + timedelta(
            minutes=settings.MAIL_VERIFICATION_COOLDOWN_MINUTES
        )
        now = datetime.now().astimezone()
        # noinspection PyTypeChecker,PydanticTypeChecker
        cooldown_left = cooldown_end - now

        if cooldown_end > now:
            raise CooldownHTTPException(
                str(int(cooldown_left.total_seconds())),
                detail=f"Too many verification requests, max 1 request per"
                f" {settings.MAIL_VERIFICATION_COOLDOWN_MINUTES}"
                f" minutes allowed",
            )

        db.delete(db_email_verification_request)

    email_verification_request = create_email_request(
        user=user_db,
        token_type=TokenType.email_verification_token,
        request_type=EmailRequestType.email_verification_request,
    )

    db.add(email_verification_request)
    db.commit()

    content_language = (
        db.query(models.Setting)
        .where(
            models.Setting.name == AvailableSettings.language
            and models.Setting.user_id == user_db.id
        )
        .first()
    )

    message, template_name = create_email_verification_email(
        content_language.current_value,
        user_db,
        email_verification_request.request_token,
    )

    background_tasks.add_task(send_email, message, template_name)

    return user_email


@router.put("/verify-email", response_model=ReturnUser)
def verify_email(
    email_verification_request: EmailVerificationRequest, db: Session = Depends(get_db)
) -> ReturnUser:
    request_db = (
        db.query(models.EmailRequests)
        .where(
            models.EmailRequests.request_type
            == EmailRequestType.email_verification_request
            and models.EmailRequests.request_token
            == email_verification_request.verification_token
        )
        .first()
    )

    if not request_db:
        raise HTTPException(
            detail="Invalid verification token provided",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token_db = request_db.request_token

    if not token_db:
        raise HTTPException(
            detail="Invalid verification token provided",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    payload = oauth2.decode_jwt(
        email_verification_request.verification_token,
        expected_token_type=TokenType.email_verification_token,
        on_error=on_decode_error,
        db=db,
        request_db=request_db,
    )

    user = db.query(models.User).where(models.User.id == payload.user_id).first()

    user.verified = True
    db.commit()
    db.refresh(user)

    return user


@router.get("/me", response_model=ReturnUser, name="Get info about your account")
def me(db: Session = Depends(get_db), user=Depends(oauth2.get_user)) -> ReturnUser:
    user_id = user.id
    user = db.query(models.User).where(models.User.id == user_id).first()

    return user


@router.get("", response_model=ReturnUsers)
def get_users(
    db: Session = Depends(get_db), _=Depends(oauth2.get_admin)
) -> dict[str, ReturnUser]:
    users_db = db.query(models.User).all()

    return {"users": users_db}


@router.put("/me/update-details", response_model=ReturnUser)
def update_user_details(
    name: str = Form(Required),
    surname: str = Form(Required),
    gender: Gender = Form(Required),
    user_credentials: OAuth2PasswordRequestFormStrict = Depends(),
    db: Session = Depends(get_db),
):
    if user_credentials.grant_type != "password":
        raise InvalidGrantTypeException("password")

    user = (
        db.query(models.User)
        .filter(models.User.email == user_credentials.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid credentials"
        )

    password_hash = (
        db.query(models.Password.password_hash)
        .where(models.Password.user_id == user.id)
        .where(models.Password.current == True)
        .first()
    )

    if not utils.compare_passwords(user_credentials.password, *password_hash):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid credentials"
        )

    user.name = name
    user.surname = surname
    user.gender = gender

    db.commit()
    db.refresh(user)

    return user


@router.get("/{uuid}", response_model=ReturnUserDetailed, name="Get User")
def get_user_by_uuid(
    uuid: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_admin)
) -> ReturnUserDetailed:
    user = get_user_from_db(uuid=uuid, db=db)

    return user


# TODO: Require auth via otps for critical administration ?
@router.put("/promote/{uuid}", response_model=ReturnUserDetailed)
def promote_user(
    uuid: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_admin)
):
    user = get_user_from_db(uuid=uuid, db=db)

    if not user.verified:
        # TODO: Cannot promote a user without 2FA on?
        raise HTTPException(
            detail="Cannot promote an unverified user",
            status_code=status.HTTP_409_CONFLICT,
        )

    if "admin" in user.permission_level:
        raise HTTPException(
            detail="This user already has the highest possible permission level",
            status_code=status.HTTP_409_CONFLICT,
        )

    user.permission_level.append("admin")

    db.commit()

    return user


@router.put("/demote/{uuid}", response_model=ReturnUserDetailed)
def demote_user(
    uuid: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_superuser)
):
    user = get_user_from_db(uuid=uuid, db=db)

    if "admin" not in user.permission_level:
        raise HTTPException(
            detail="This user already has the lowest possible permission level",
            status_code=status.HTTP_409_CONFLICT,
        )

    user.permission_level.pop("admin")

    db.commit()

    return user


@router.put("/ban/{uuid}", response_model=ReturnUserDetailed)
def ban_user(uuid: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_admin)):
    user = get_user_from_db(uuid=uuid, db=db)

    if "admin" in user.permission_level:
        raise HTTPException(
            detail="Cannot ban user with elevated permissions level, if you are a superuser and really"
            "want to perform this action, you need to demote this user first",
            status_code=status.HTTP_409_CONFLICT,
        )

    user.disabled = True

    db.commit()

    return user


@router.put("/unban/{uuid}", response_model=ReturnUserDetailed)
def unban_user(uuid: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_admin)):
    user = get_user_from_db(uuid=uuid, db=db)

    if not user.disabled:
        raise HTTPException(
            detail="This user is not currently banned",
            status_code=status.HTTP_409_CONFLICT,
        )

    user.disabled = False

    db.commit()

    return user
