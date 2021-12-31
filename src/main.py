from fastapi import FastAPI
from .routers import users, auth
from .config import settings

app = FastAPI(docs_url=settings.BASE_URL + '/docs',
              redoc_url=settings.BASE_URL + '/redoc',
              openapi_url=settings.BASE_URL + '/openapi.json',
              title='Zołza Hairstyles API',
              version='0.1 Alpha')

app.include_router(users.router)
app.include_router(auth.router)


@app.get(settings.BASE_URL + '/', tags=['Hello World Test'])
async def root():
    return {"Response": "Hello World"}
