from fastapi import FastAPI
from fastapi import APIRouter

app = FastAPI()

router = APIRouter(prefix='/api')

app.include_router(router)


@router.get('/')
async def root():
    return {"Response": "Hello World"}
