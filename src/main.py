from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import github_client
from .config import settings
from .loggers import app_logger
from .routers import appointments, auth, notifications, services, user_settings, users
from .scheduler import configure_and_start_scheduler

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
    app_logger.info("Application is in startup")

    configure_and_start_scheduler()


@app.get(settings.BASE_URL, tags=["Zołza Hairstyles Redirection"])
def zolza_hairstyles_redirection():
    return RedirectResponse(
        settings.ZOLZA_HAIRSTYLES_URL, status_code=status.HTTP_308_PERMANENT_REDIRECT
    )


@app.get(settings.BASE_URL + "/github_user/{username}")
def get_github_user_data(username: str):
    if not settings.GH_APP_CLIENT_ID or settings.GH_APP_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Path not found"
        )

    data = github_client.get_user_data(username)

    return data
