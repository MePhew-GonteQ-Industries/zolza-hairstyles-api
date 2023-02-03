import datetime
import logging

import langcodes
import pytz
import user_agents
from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import UUID4
from sqlalchemy.orm import Session

from src import models
from .ipinfo import get_ip_address_details
from .schemas.session import (
    BrowserInfo,
    DeviceInfo,
    LocationData,
    LoginData,
    OsInfo,
    UserAgentInfo,
)
from .schemas.user_settings import AvailableSettings, DefaultContentLanguages

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

formatter = logging.Formatter(
    "%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S"
)
file_handler = logging.FileHandler(f"utils.log")
file_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


def get_language_code_from_header(accept_language: str):
    if accept_language:
        accept_language = accept_language.split(",")[0].split(";")[0]
        language = langcodes.Language.get(langcodes.standardize_tag(accept_language))

        if language.is_valid():
            language_code = language.language
        else:
            language_code = DefaultContentLanguages.polish.value
    else:
        language_code = DefaultContentLanguages.polish.value

    return language_code


def get_language_id_from_language_code(db: Session, language_code: str):
    language_id = (
        db.query(models.Language.id)
        .where(models.Language.code == language_code)
        .first()
    )

    if language_id:
        language_id = language_id[0]

    if not language_id:
        language_id = (
            db.query(models.Language.id)
            .where(models.Language.code == DefaultContentLanguages.english)
            .first()[0]
        )

    return language_id


def get_user_language_id(db: Session, user_id: UUID4) -> int:
    language_code = (
        db.query(models.Setting.current_value)
        .where(models.Setting.name == AvailableSettings.language.value)
        .where(models.Setting.user_id == user_id)
        .first()
    )

    if language_code:
        language_code = language_code[0]

    language_id = get_language_id_from_language_code(db, language_code)

    return language_id


def verify_password(*, password, user_id, db) -> None:
    current_password_hash = (
        db.query(models.Password.password_hash)
        .where(models.Password.user_id == user_id)
        .where(models.Password.current == True)
        .first()
    )

    if not compare_passwords(password, *current_password_hash):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid credentials"
        )


def change_password(*, new_password, user_id, db: Session) -> None:
    recent_passwords = (
        db.query(models.Password).where(models.Password.user_id == user_id).all()
    )

    for recent_password in recent_passwords:
        if compare_passwords(new_password, recent_password.password_hash):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="new password cannot be the same as any of the last 5 passwords",
            )

    old_passwords = (
        db.query(models.Password)
        .where(models.Password.user_id == user_id)
        .where(models.Password.current == False)
        .order_by(models.Password.created_at.desc())
        .offset(4)
        .all()
    )

    for old_password in old_passwords:
        db.delete(old_password)

    db.commit()

    current_password = (
        db.query(models.Password)
        .where(models.Password.user_id == user_id)
        .where(models.Password.current)
        .first()
    )

    current_password.current = False

    db.commit()

    new_password = models.Password(
        password_hash=hash_password(new_password),
        user_id=user_id,
        current=True,
    )

    db.add(new_password)

    db.commit()


def hash_password(password) -> str:
    return pwd_context.hash(password)


def compare_passwords(plain_text_password, hashed_password) -> bool:
    return pwd_context.verify(plain_text_password, hashed_password)


def on_decode_error(*, db, request_db) -> None:
    db.delete(request_db)
    db.commit()


def get_user_from_db(*, uuid: UUID4, db: Session):
    user = db.query(models.User).where(models.User.id == uuid).first()

    if not user:
        raise HTTPException(
            detail=f"User with uuid of {uuid} does not exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return user


def get_user_agent_info(user_agent: str) -> user_agents.parsers.UserAgent:
    return user_agents.parse(user_agent)


def load_session_data(session_db: models.Session):
    sign_in_user_agent_info = get_user_agent_info(session_db.sign_in_user_agent)
    sign_in_user_agent_info = UserAgentInfo(
        is_bot=sign_in_user_agent_info.is_bot,
        device=DeviceInfo(
            brand=sign_in_user_agent_info.device.brand,
            family=sign_in_user_agent_info.device.family,
            model=sign_in_user_agent_info.device.model,
            is_mobile=sign_in_user_agent_info.is_mobile,
            is_tablet=sign_in_user_agent_info.is_tablet,
            is_pc=sign_in_user_agent_info.is_pc,
            supports_touch=sign_in_user_agent_info.is_touch_capable,
        ),
        os=OsInfo(
            family=sign_in_user_agent_info.os.family,
            version=sign_in_user_agent_info.os.version_string,
        ),
        browser=BrowserInfo(
            family=sign_in_user_agent_info.browser.family,
            version=sign_in_user_agent_info.browser.version_string,
        ),
    )
    sign_in_data = LoginData(
        user_agent=session_db.sign_in_user_agent,
        ip_address=session_db.sign_in_ip_address,
        location=None,
        user_agent_info=sign_in_user_agent_info,
    )
    sign_in_ip_address_details = get_ip_address_details(session_db.sign_in_ip_address)
    if sign_in_ip_address_details:
        location_data = LocationData(
            city=sign_in_ip_address_details.get("city"),
            region=sign_in_ip_address_details.get("region"),
            country=sign_in_ip_address_details.get("country"),
            longitude=sign_in_ip_address_details.get("longitude"),
            latitude=sign_in_ip_address_details.get("latitude"),
        )
        sign_in_data.location = location_data
    session_db.sign_in_data = sign_in_data

    last_user_agent_info = get_user_agent_info(session_db.last_user_agent)
    last_user_agent_info = UserAgentInfo(
        is_bot=last_user_agent_info.is_bot,
        device=DeviceInfo(
            brand=last_user_agent_info.device.brand,
            family=last_user_agent_info.device.family,
            model=last_user_agent_info.device.model,
            is_mobile=last_user_agent_info.is_mobile,
            is_tablet=last_user_agent_info.is_tablet,
            is_pc=last_user_agent_info.is_pc,
            supports_touch=last_user_agent_info.is_touch_capable,
        ),
        os=OsInfo(
            family=last_user_agent_info.os.family,
            version=last_user_agent_info.os.version_string,
        ),
        browser=BrowserInfo(
            family=last_user_agent_info.browser.family,
            version=last_user_agent_info.browser.version_string,
        ),
    )
    last_access_data = LoginData(
        user_agent=session_db.last_user_agent,
        ip_address=session_db.last_ip_address,
        location=None,
        user_agent_info=last_user_agent_info,
    )
    last_ip_address_details = get_ip_address_details(session_db.last_ip_address)
    if last_ip_address_details:
        location_data = LocationData(
            city=last_ip_address_details.get("city"),
            region=last_ip_address_details.get("region"),
            country=last_ip_address_details.get("country"),
            longitude=last_ip_address_details.get("longitude"),
            latitude=last_ip_address_details.get("latitude"),
        )
        last_access_data.location = location_data
    session_db.last_access_data = last_access_data

    return session_db


PL_TIMEZONE = pytz.timezone("Poland")


def is_archival(appointment: models.Appointment):
    return appointment.end_slot.end_time < datetime.datetime.now(PL_TIMEZONE)


def format_datetime_str(datetime_obj: datetime.datetime) -> str:
    return datetime_obj.strftime("%d.%m.%Y, %H:%M")
