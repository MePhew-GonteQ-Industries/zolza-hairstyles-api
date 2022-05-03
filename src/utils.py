import calendar
import json
import logging
import math
import os
from datetime import date, datetime, timedelta

import langcodes
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import HTTPException, status
from langcodes import standardize_tag
from passlib.context import CryptContext
from pydantic import UUID4
from sqlalchemy.orm import Session

from src import models
from .config import settings
from .database import SQLALCHEMY_DATABASE_URL, get_db
from .scheduler import configure_scheduler, scheduler
from .schemas.user_settings import AvailableSettings, DefaultContentLanguages

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logging.basicConfig(filename='ZHAPI_log.log', encoding='utf-8', level=logging.DEBUG)


def init_languages(db: Session) -> None:
    english = langcodes.Language.get(standardize_tag("en-GB"))

    english_db = (
        db.query(models.Language)
        .where(models.Language.code == english.language)
        .first()
    )

    if not english_db:
        english = models.Language(code=english.language, name=english.language_name())
        db.add(english)

        logging.debug(f'English was not found in db (value = {english_db})')

    polish = langcodes.Language.get(standardize_tag("pl-PL"))

    polish_db = (
        db.query(models.Language).where(models.Language.code == polish.language).first()
    )

    if not polish_db:
        polish = models.Language(code=polish.language, name=polish.language_name())
        db.add(polish)

        logging.debug(f'Polish was not found in db (value = {english_db})')

    db.commit()


def init_services(db: Session) -> None:
    dir_name = os.path.dirname(__file__)
    services_path = os.path.join(dir_name, f"resources/services.json")

    with open(services_path, encoding="utf-8") as services:
        services = json.loads(services.read())

    for service in services:
        names = service["name"]

        service_in_db = False

        for lang, name in names.items():
            service_translation = (
                db.query(models.ServiceTranslations)
                .where(models.ServiceTranslations.name == name)
                .first()
            )

            if service_translation:
                service_in_db = True

        if not service_in_db:
            service_db = models.Service(
                min_price=service["min_price"],
                max_price=service["max_price"],
                average_time_minutes=service["average_time_minutes"],
                required_slots=(
                    int(service["average_time_minutes"])
                    // settings.APPOINTMENT_SLOT_TIME_MINUTES
                ),
            )
            db.add(service_db)
            db.commit()
            db.refresh(service_db)

            for lang, name in names.items():
                logging.debug(f'Service {name} was not found in the database')

                language_db = (
                    db.query(models.Language)
                    .where(models.Language.code == lang)
                    .first()
                )

                service_translation = models.ServiceTranslations(
                    service_id=service_db.id, language_id=language_db.id, name=name
                )
                db.add(service_translation)
                db.commit()


def init_holidays(db: Session) -> None:
    dir_name = os.path.dirname(__file__)
    holiday_names = os.path.join(dir_name, "resources/holiday_names.json")

    with open(holiday_names, "r", encoding="utf-8") as holiday_names:
        holiday_names = json.loads(holiday_names.read())

    for holiday in holiday_names:

        holiday_in_db = False

        for lang, name in holiday.items():
            holiday_db = (
                db.query(models.Holiday)
                .join(models.HolidayTranslations)
                .where(models.HolidayTranslations.name == name)
                .first()
            )

            if holiday_db:
                holiday_in_db = True

        if not holiday_in_db:
            holiday_db = models.Holiday()
            db.add(holiday_db)
            db.commit()
            db.refresh(holiday_db)

            for lang, name in holiday.items():
                language_db = (
                    db.query(models.Language)
                    .where(models.Language.code == lang)
                    .first()
                )

                holiday_translation = models.HolidayTranslations(
                    holiday_id=holiday_db.id, language_id=language_db.id, name=name
                )
                db.add(holiday_translation)
                db.commit()


def ensure_enough_appointment_slots_available(get_db_func: callable) -> None:
    db = next(get_db_func())

    if not appointment_slots_generated(db):
        generate_appointment_slots(db)


def ensure_appointment_slots_generation_task_exists(
    background_scheduler: BackgroundScheduler,
) -> None:
    appointment_slots_generation_task = background_scheduler.get_job(
        "appointment_slots_generation"
    )

    if not appointment_slots_generation_task:
        add_appointment_slots_generation_task(background_scheduler)


def add_appointment_slots_generation_task(
    background_scheduler: BackgroundScheduler,
) -> None:
    background_scheduler.add_job(
        ensure_enough_appointment_slots_available,
        args=[get_db],
        trigger="interval",
        days=1,
        name="Appointment Slots Generation",
        next_run_time=datetime.now() + timedelta(days=1),
        coalesce=True,
        max_instances=1,
        id="appointment_slots_generation",
    )


def appointment_slots_generated(db: Session) -> bool:
    last_appointment_slot = (
        db.query(models.AppointmentSlot)
        .order_by(models.AppointmentSlot.date.desc())
        .first()
    )

    if not last_appointment_slot:
        return False

    now = date.today()

    days = 366 if calendar.isleap(now.year) else 365

    next_year = now + timedelta(days=days)

    if last_appointment_slot.date < next_year:
        return False

    return True


def generate_appointment_slots(db: Session) -> None:
    sunday = 6

    dir_name = os.path.dirname(__file__)
    holiday_names = os.path.join(dir_name, "resources/holiday_names.json")
    holiday_dates = os.path.join(dir_name, "resources/holiday_dates.json")
    weekplan = os.path.join(dir_name, "dynamic_resources/weekplan.json")

    with open(holiday_names, "r", encoding="utf-8") as holiday_names:
        holiday_names = json.loads(holiday_names.read())

    holiday_ids = []
    for holiday in holiday_names:
        holiday_id = (
            db.query(models.Holiday.id)
            .join(models.HolidayTranslations)
            .where(models.HolidayTranslations.name == list(holiday.values())[0])
            .first()[0]
        )
        holiday_ids.append(holiday_id)

    with open(holiday_dates, "r", encoding="utf-8") as holiday_dates:
        holiday_dates = json.loads(holiday_dates.read())

    with open(weekplan, "r", encoding="utf-8") as weekplan:
        weekplan = json.loads(weekplan.read())

    start_hours = [day["work_hours"]["start_hour"] for day in weekplan]
    start_minutes = [day["work_hours"]["start_minute"] for day in weekplan]
    first_hours_indices = [
        index for index, item in enumerate(start_hours) if item == min(start_hours)
    ]
    first_start_hour = min(start_hours)
    first_start_minute = max(
        [
            minute
            for index, minute in enumerate(start_minutes)
            if index in first_hours_indices
        ]
    )

    end_hours = [day["work_hours"]["end_hour"] for day in weekplan]
    end_minutes = [day["work_hours"]["end_minute"] for day in weekplan]

    last_end_hours_indices = [
        index for index, item in enumerate(end_hours) if item == max(end_hours)
    ]

    last_end_hour = max(end_hours)
    last_end_minute = max(
        [
            minute
            for index, minute in enumerate(end_minutes)
            if index in last_end_hours_indices
        ]
    )

    last_appointment_slot = (
        db.query(models.AppointmentSlot)
        .order_by(models.AppointmentSlot.end_time.desc().nullslast())
        .first()
    )

    first_slot_start = None

    now = datetime.now()

    if last_appointment_slot:
        if last_appointment_slot.end_time:
            first_slot_start = last_appointment_slot.end_time
        else:
            last_appointment_slot_date = last_appointment_slot.date

            first_slot_start = now.replace(
                year=last_appointment_slot_date.year,
                month=last_appointment_slot_date.month,
                day=last_appointment_slot_date.day + 1,
                hour=first_start_hour,
                minute=first_start_minute,
                second=0,
                microsecond=0,
            )

    if not first_slot_start:
        hours = now.hour

        minutes = settings.APPOINTMENT_SLOT_TIME_MINUTES * math.ceil(
            now.minute / settings.APPOINTMENT_SLOT_TIME_MINUTES
        )

        if minutes == 60:
            hours = now.hour + 1 if now.hour + 1 < 24 else 0
            minutes = 0

        first_slot_start = now.replace(
            hour=hours, minute=minutes, second=0, microsecond=0
        )

    days = 366 if calendar.isleap(now.year) else 365

    last_slot_end = now + timedelta(days=days)

    last_slot_end = last_slot_end.replace(
        hour=last_end_hour, minute=last_end_minute, second=0, microsecond=0
    )

    current_date = first_slot_start

    while current_date < last_slot_end:
        temp_date = current_date
        appointment_slot = None

        test_date = current_date.strftime("%d.%m")

        if test_date in holiday_dates[str(current_date.year)]:
            index = holiday_dates[str(current_date.year)].index(test_date)

            if current_date.weekday() == sunday:
                appointment_slot = models.AppointmentSlot(
                    date=current_date,
                    sunday=True,
                    holiday=True,
                    holiday_id=holiday_ids[index],
                )
            else:
                appointment_slot = models.AppointmentSlot(
                    date=current_date, holiday=True, holiday_id=holiday_ids[index]
                )

            current_date = current_date + timedelta(days=1)
            next_day_index = current_date.weekday() + 1
            hour = (
                weekplan[next_day_index]["work_hours"]["start_hour"]
                if next_day_index <= 5
                else first_start_hour
            )
            minute = (
                weekplan[next_day_index]["work_hours"]["start_minute"]
                if next_day_index <= 5
                else first_start_minute
            )
            current_date = current_date.replace(hour=hour, minute=minute)
        else:
            if current_date.weekday() == sunday:
                appointment_slot = models.AppointmentSlot(
                    date=current_date, sunday=True
                )
                current_date = current_date.replace(
                    hour=first_start_hour, minute=first_start_minute
                )
                current_date = current_date + timedelta(days=1)
            else:
                if (
                    current_date.hour
                    < weekplan[current_date.weekday()]["work_hours"]["start_hour"]
                ):
                    current_date = current_date.replace(
                        hour=weekplan[current_date.weekday()]["work_hours"][
                            "start_hour"
                        ],
                        minute=weekplan[current_date.weekday()]["work_hours"][
                            "start_minute"
                        ],
                    )
                    continue
                elif (
                    current_date.hour
                    > weekplan[current_date.weekday()]["work_hours"]["end_hour"]
                ):
                    current_date = current_date + timedelta(days=1)
                    next_day_index = current_date.weekday() + 1
                    hour = (
                        weekplan[next_day_index]["work_hours"]["start_hour"]
                        if next_day_index <= 5
                        else first_start_hour
                    )
                    minute = (
                        weekplan[next_day_index]["work_hours"]["start_minute"]
                        if next_day_index <= 5
                        else first_start_minute
                    )

                    current_date = current_date.replace(hour=hour, minute=minute)
                    continue
                elif (
                    current_date.hour
                    == weekplan[current_date.weekday()]["work_hours"]["end_hour"]
                ):
                    if (
                        current_date.minute
                        >= weekplan[current_date.weekday()]["work_hours"]["end_minute"]
                    ):
                        current_date = current_date + timedelta(days=1)
                        next_day_index = current_date.weekday() + 1
                        hour = (
                            weekplan[next_day_index]["work_hours"]["start_hour"]
                            if next_day_index <= 5
                            else first_start_hour
                        )
                        minute = (
                            weekplan[next_day_index]["work_hours"]["start_minute"]
                            if next_day_index <= 5
                            else first_start_minute
                        )

                        current_date = current_date.replace(hour=hour, minute=minute)
                        continue

                for break_time in weekplan[current_date.weekday()]["breaks"]:
                    if current_date.hour == break_time["start_hour"]:
                        if current_date.minute == break_time["start_minute"]:
                            appointment_slot = models.AppointmentSlot(
                                date=current_date,
                                start_time=current_date,
                                end_time=current_date
                                + timedelta(minutes=break_time["time_minutes"]),
                                break_time=True,
                            )
                            current_date = current_date + timedelta(
                                minutes=break_time["time_minutes"]
                            )

        if not appointment_slot:
            appointment_slot = models.AppointmentSlot(
                date=current_date,
                start_time=current_date,
                end_time=(
                    current_date
                    + timedelta(minutes=settings.APPOINTMENT_SLOT_TIME_MINUTES)
                ),
            )

        db.add(appointment_slot)

        if current_date == temp_date:
            current_date = current_date + timedelta(
                minutes=settings.APPOINTMENT_SLOT_TIME_MINUTES
            )

    db.commit()


def start_scheduler() -> BackgroundScheduler:
    configure_scheduler(SQLALCHEMY_DATABASE_URL)
    scheduler.start()

    return scheduler


def get_user_language_id(db: Session, user_id: UUID4) -> int:
    language_code = (
        db.query(models.Setting.current_value)
        .where(models.Setting.name == AvailableSettings.language.value)
        .where(models.Setting.user_id == user_id)
        .first()
    )

    if language_code:
        language_code = language_code[0]

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
