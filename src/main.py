from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, auth, user_settings, appointments, services
from .config import settings


app = FastAPI(docs_url=settings.BASE_URL + '/docs',
              redoc_url=settings.BASE_URL + '/redoc',
              openapi_url=settings.BASE_URL + '/openapi.json',
              title=settings.API_TITLE,
              version=settings.API_VERSION)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(user_settings.router)
app.include_router(appointments.router)
app.include_router(services.router)

ALLOWED_ORIGINS = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(settings.BASE_URL, tags=['Zołza Hairstyles Redirection'])
async def zolza_hairstyles_redirection():
    return RedirectResponse(settings.ZOLZA_HAIRSTYLES_URL,
                            status_code=status.HTTP_308_PERMANENT_REDIRECT)
