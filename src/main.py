import logging
import threading

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse

from .config import settings
from .database import get_db
from .routers import appointments, auth, services, user_settings, users
from .utils import (
    ensure_appointment_slots_generation_task_exists,
    ensure_enough_appointment_slots_available,
    init_holidays,
    init_languages,
    init_services,
    start_scheduler,
)

logging.basicConfig(
    filename="app.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s;%(levelname)s;%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

formatter = logging.Formatter(
    "%(thread)d;%(threadName)s;%(asctime)s;%(levelname)s;%(message)s",
    "%Y-%m-%d %H:%M:%S",
)

file_handler = logging.FileHandler(f"main.log", mode="w")
file_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

app = FastAPI(
    docs_url=settings.BASE_URL + "/docs",
    redoc_url=settings.BASE_URL + "/redoc",
    openapi_url=settings.BASE_URL + "/openapi.json",
    title=settings.API_TITLE,
    version=settings.API_VERSION,
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(user_settings.router)
app.include_router(appointments.router)
app.include_router(services.router)


@app.on_event("startup")
def startup():
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


@app.get(settings.BASE_URL, tags=["Zołza Hairstyles Redirection"])
async def zolza_hairstyles_redirection():
    return RedirectResponse(
        settings.ZOLZA_HAIRSTYLES_URL, status_code=status.HTTP_308_PERMANENT_REDIRECT
    )
