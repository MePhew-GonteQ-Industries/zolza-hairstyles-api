import logging

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .database import SQLALCHEMY_DATABASE_URL
from .routers import appointments, auth, services, user_settings, users, notifications
from .scheduler import configure_and_start_scheduler
from . import github_client

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

file_handler = logging.FileHandler(f"main.log")
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
app.include_router(notifications.router)

ALLOWED_ORIGINS = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    logger.info("Application is in startup")

    configure_and_start_scheduler(SQLALCHEMY_DATABASE_URL)


@app.get(settings.BASE_URL, tags=["Zołza Hairstyles Redirection"])
def zolza_hairstyles_redirection():
    return RedirectResponse(
        settings.ZOLZA_HAIRSTYLES_URL, status_code=status.HTTP_308_PERMANENT_REDIRECT
    )


@app.get(settings.BASE_URL + '/github_user/{username}')
def get_github_user_data(username: str):
    data = github_client.get_user_data(username)

    return data
