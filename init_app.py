import logging

from src.database import get_db
from src.utils import (
    ensure_appointment_slots_generation_task_exists,
    ensure_enough_appointment_slots_available,
    init_holidays,
    init_languages,
    init_services,
    start_scheduler,
)

formatter = logging.Formatter(
    "%(thread)d;%(threadName)s;%(asctime)s;%(levelname)s;%(message)s",
    "%Y-%m-%d %H:%M:%S",
)

file_handler = logging.FileHandler(f"init_app.log")
file_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


def init_app():
    logger.info("Application is in startup")

    scheduler = start_scheduler()

    logger.info("Scheduler started")

    db = next(get_db())

    logger.info(f"Created new {type(db)} object #{id(db)}")

    init_languages(db)

    logger.info(f"Successfully initialized languages using {type(db)} object #{id(db)}")

    init_services(db)

    logger.info(f"Successfully initialized services using {type(db)} object #{id(db)}")

    init_holidays(db)

    logger.info(f"Successfully initialized holidays using {type(db)} object #{id(db)}")

    ensure_enough_appointment_slots_available(get_db)

    ensure_appointment_slots_generation_task_exists(scheduler)
