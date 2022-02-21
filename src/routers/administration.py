from fastapi import APIRouter
from ..config import settings

router = APIRouter(
    prefix=settings.BASE_URL + "/administration", tags=["Administration"]
)


@router.post("/get-stats")
def get_stats():
    raise NotImplementedError
