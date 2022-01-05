from fastapi import FastAPI
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


@app.get(settings.BASE_URL + '/', tags=['Hello World Test'])
async def root():
    return {"Message": "Welcome to Zołza Hairstyles API!"}
