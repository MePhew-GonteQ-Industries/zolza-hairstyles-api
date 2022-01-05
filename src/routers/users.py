from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException, Header
from ..config import settings
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.user import CreateUser, ReturnUser, ReturnUserAndSettings
from ..schemas.user_settings import AvailableContentLanugages, AvailableThemes, PreferedTheme, Language
from .. import models
from fastapi_mail import MessageSchema
from ..email import send_email
from sqlalchemy.exc import IntegrityError
from pydantic import Required

router = APIRouter(prefix=settings.BASE_URL + '/users',
                   tags=['Users'])


@router.post('/register', status_code=status.HTTP_201_CREATED, response_model=ReturnUserAndSettings)
def create_user(user: CreateUser,
                background_tasks: BackgroundTasks,
                db: Session = Depends(get_db),
                content_language: AvailableContentLanugages = Header(Required),
                prefered_theme: AvailableThemes = Header(Required)):
    """
    ## Part of the user creation process is initializing the user's settings
    ### For this reason it is required to pass two *header parameters*: `content-language` and `prefered-theme` to this endpoint
    ### Later on these settings can be accessed and modified via *`/api/settings/`* endpoint

    #### `content-language` is a **required** *header parameter* used to represent user's prefered content language.

    It can only be set to one of the following two values as these are the only languages currently supported
    both by this API and [Zołza Hairstyles](https://mephew.ddns.net) website :
    - **pl** for Polish content
    - **en** for English content

    This value will be saved in the database as the user's language in the created user's settings.

    This particular endpoint uses this value to determine the apropriate language of the account activation message
    sent to the user after the account is created.

    Other endpoints use this value in a similiar manner (e.g. when sending messages related to 2FA setup, user
    permissions updates or upcoming appointments notices)


    #### `prefered-theme` is a **required** *header parameter* used to represent user's prefered application theme

    It can only be set to one of the following two values as these are the only themes currently supported
    by [Zołza Hairstyles](https://mephew.ddns.net) website :
    - **dark** for dark theme
    - **light** for light theme

    This value will be saved in the database as the user's prefered theme in the created user's settings.

    This particular endpoint uses this value only for the sole purpose of user config initialization in order to
    provide consistent theming experience across multiple devices and/or web browsers
    """

    user_theme = PreferedTheme(current_value=prefered_theme)

    if content_language == content_language.polish:
        template_name = 'account_verification_pl.html'
        subject = 'Zołza Hairstyles - weryfikacja konta'
        user_language = Language(current_value=AvailableContentLanugages.polish)
    elif content_language == content_language.english:
        template_name = 'account_verification_en.html'
        subject = 'Zołza Hairstyles - account verification'
        user_language = Language(current_value=AvailableContentLanugages.english)
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=[
                                {
                                    "loc": [
                                        "header",
                                        "content-language"
                                    ],
                                    "msg": "value is not a valid enumeration member; permitted: 'pl', 'en'",
                                    "type": "type_error.enum",
                                    "ctx": {
                                        "enum_values": [
                                            "pl",
                                            "en"
                                        ]
                                    }
                                }
                            ])

    message = MessageSchema(
        subject=subject,
        recipients=[user.email],
        template_body={
            'user': user.name,
            'account_confirmation_link': 'https://mephew.ddns.net/account/activate/213414'
        },
        subtype="html"
    )

    background_tasks.add_task(send_email, message, template_name)

    new_user = user.dict()
    new_user['hashed_password'] = new_user.pop('password')

    new_user = models.User(**new_user)
    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='duplicate key value violates unique constraint user_email')

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

    return {'user': new_user,
            'settings': user_settings}


@router.get('/me', response_model=ReturnUser)
async def me(db: Session = Depends(get_db)):
    # user = db.query(models.User).filter(models.User.id == user_id)

    return {'test': 'success'}
