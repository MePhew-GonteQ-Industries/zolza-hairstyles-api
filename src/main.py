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
    scheduler = start_scheduler()

    db = next(get_db())

    init_languages(db)

    init_services(db)

    init_holidays(db)

    ensure_enough_appointment_slots_available(get_db)

    ensure_appointment_slots_generation_task_exists(scheduler)


@app.get(settings.BASE_URL, tags=["Zołza Hairstyles Redirection"])
async def zolza_hairstyles_redirection():
    return RedirectResponse(
        settings.ZOLZA_HAIRSTYLES_URL, status_code=status.HTTP_308_PERMANENT_REDIRECT
    )
