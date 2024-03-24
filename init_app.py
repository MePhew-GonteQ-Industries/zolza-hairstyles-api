import calendar
import json
import math
import os
from datetime import date, datetime, timedelta
from typing import Any

import langcodes
from apscheduler.schedulers.background import BackgroundScheduler
from langcodes import standardize_tag
from sqlalchemy.orm import Session

from src import models
from src.config import settings
from src.database import get_db
from src.loggers import init_app_logger
from src.scheduler import configure_and_start_scheduler, scheduler
from src.utils import PL_TIMEZONE


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

    polish = langcodes.Language.get(standardize_tag("pl-PL"))

    polish_db = (
        db.query(models.Language).where(models.Language.code == polish.language).first()
    )

    if not polish_db:
        polish = models.Language(code=polish.language, name=polish.language_name())
        db.add(polish)

    try:
        db.commit()
    except Exception as e:
        init_app_logger.error(
            f"Initializing languages with {type(db)} instance failed with error {e}"
        )
        raise


def load_json_file(file_path: str) -> Any:
    dir_name = os.path.dirname(__file__)
    path = os.path.join(dir_name, file_path)

    with open(path, encoding="utf-8") as file:
        json_content = json.loads(file.read())
        return json_content


def init_services(db: Session) -> None:
    services = load_json_file("resources/services.json")

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
                description=service.get("description"),
            )
            db.add(service_db)
            db.commit()
            db.refresh(service_db)

            for lang, name in names.items():
                language_db = (
                    db.query(models.Language)
                    .where(models.Language.code == lang)
                    .first()
                )

                service_translation = models.ServiceTranslations(
                    service_id=service_db.id, language_id=language_db.id, name=name
                )
                db.add(service_translation)
                try:
                    db.commit()
                except Exception as e:
                    init_app_logger.error(
                        f"Adding service translation with {type(db)} instance"
                        f"failed with error {e}"
                    )
                    raise


def check_if_holiday_in_db(holiday: dict, db: Session) -> bool:
    for lang, name in holiday.items():
        holiday_db = (
            db.query(models.Holiday)
            .join(models.HolidayTranslations)
            .where(models.HolidayTranslations.name == name)
            .first()
        )

        if holiday_db:
            return True

    return False


def add_holiday_to_db(db: Session) -> models.Holiday:
    holiday_db = models.Holiday()
    db.add(holiday_db)
    try:
        db.commit()
    except Exception as e:
        init_app_logger.error(
            f"Adding holiday with {type(db)} instance failed with error {e}"
        )
        raise
    db.refresh(holiday_db)

    return holiday_db


def add_holiday_translation_to_db(
    holiday: models.Holiday, lang, holiday_name: str, db: Session
) -> None:
    language_db = db.query(models.Language).where(models.Language.code == lang).first()

    holiday_translation = models.HolidayTranslations(
        holiday_id=holiday.id, language_id=language_db.id, name=holiday_name
    )
    db.add(holiday_translation)
    try:
        db.commit()
    except Exception as e:
        init_app_logger.error(
            f"Adding holiday translation with {type(db)} instance"
            f"failed with error {e}"
        )
        raise


def init_holidays(db: Session) -> None:
    holiday_names = load_json_file("resources/holiday_names.json")

    for holiday in holiday_names:
        holiday_in_db = check_if_holiday_in_db(holiday, db)

        if not holiday_in_db:
            holiday_db = add_holiday_to_db(db)

            for lang, name in holiday.items():
                add_holiday_translation_to_db(holiday_db, lang, name, db)


def ensure_enough_appointment_slots_available(get_db_func: callable) -> None:
    db = next(get_db_func())

    if not check_if_appointment_slots_generated(db):
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
        next_run_time=datetime.utcnow() + timedelta(days=1),
        coalesce=True,
        max_instances=1,
        id="appointment_slots_generation",
    )


def check_if_appointment_slots_generated(db: Session) -> bool:
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

    holiday_dates = load_json_file("resources/holiday_dates.json")
    holiday_names = load_json_file("resources/holiday_names.json")
    weekplan = load_json_file("dynamic_resources/weekplan.json")

    holiday_ids = []
    for holiday in holiday_names:
        holiday_id = (
            db.query(models.Holiday.id)
            .join(models.HolidayTranslations)
            .where(models.HolidayTranslations.name == list(holiday.values())[0])
            .first()[0]
        )
        holiday_ids.append(holiday_id)

    start_hours = [day["work_hours"]["start_hour"] for day in weekplan]
    first_hours_indices = [
        index for index, item in enumerate(start_hours) if item == min(start_hours)
    ]
    first_start_hour = min(start_hours)

    start_minutes = [day["work_hours"]["start_minute"] for day in weekplan]
    first_start_minute = min(
        [
            minute
            for index, minute in enumerate(start_minutes)
            if index in first_hours_indices
        ]
    )

    end_hours = [day["work_hours"]["end_hour"] for day in weekplan]
    last_end_hours_indices = [
        index for index, item in enumerate(end_hours) if item == max(end_hours)
    ]
    last_end_hour = max(end_hours)

    end_minutes = [day["work_hours"]["end_minute"] for day in weekplan]
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

    now = datetime.utcnow()

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
            ).astimezone(tz=PL_TIMEZONE)

    if not first_slot_start:
        hours = now.hour

        minutes = settings.APPOINTMENT_SLOT_TIME_MINUTES * math.ceil(
            now.minute / settings.APPOINTMENT_SLOT_TIME_MINUTES
        )

        if minutes == 60:
            hours = now.hour + 1 if now.hour + 1 < 24 else 0
            minutes = 0

        if hours == 0:
            first_slot_start = now.replace(
                hour=hours,
                minute=minutes,
                second=0,
                microsecond=0,
                day=now.day + 1,
            ).astimezone(tz=PL_TIMEZONE)
        else:
            first_slot_start = now.replace(
                hour=hours,
                minute=minutes,
                second=0,
                microsecond=0,
            ).astimezone(tz=PL_TIMEZONE)

    days = 366 if calendar.isleap(now.year) else 365

    last_slot_end = now + timedelta(days=days)

    last_slot_end = last_slot_end.replace(
        hour=last_end_hour, minute=last_end_minute, second=0, microsecond=0
    ).astimezone(PL_TIMEZONE)

    current_date = first_slot_start

    appointment_slots = []

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
                                start_time=current_date.astimezone(PL_TIMEZONE),
                                end_time=current_date.astimezone(PL_TIMEZONE)
                                + timedelta(minutes=break_time["time_minutes"]),
                                break_time=True,
                            )
                            current_date = current_date + timedelta(
                                minutes=break_time["time_minutes"]
                            )

        if not appointment_slot:
            appointment_slot = models.AppointmentSlot(
                date=current_date,
                start_time=current_date.astimezone(PL_TIMEZONE),
                end_time=(
                    current_date.astimezone(PL_TIMEZONE)
                    + timedelta(minutes=settings.APPOINTMENT_SLOT_TIME_MINUTES)
                ),
            )

        appointment_slots.append(appointment_slot)

        if current_date == temp_date:
            current_date = current_date + timedelta(
                minutes=settings.APPOINTMENT_SLOT_TIME_MINUTES
            )

    if appointment_slots:
        db.add_all(appointment_slots)
        db.commit()


def init_app():
    init_app_logger.info("Initializing application")

    configure_and_start_scheduler()

    init_app_logger.info("Scheduler started")

    db = next(get_db())

    init_app_logger.info(f"Created new {type(db)} object #{id(db)}")

    init_languages(db)

    init_app_logger.info(
        f"Successfully initialized languages using {type(db)} object #{id(db)}"
    )

    init_services(db)

    init_app_logger.info(
        f"Successfully initialized services using {type(db)} object #{id(db)}"
    )

    init_holidays(db)

    init_app_logger.info(
        f"Successfully initialized holidays using {type(db)} object #{id(db)}"
    )

    ensure_enough_appointment_slots_available(get_db)

    ensure_appointment_slots_generation_task_exists(scheduler)
