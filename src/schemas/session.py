from pydantic import BaseModel
from pydantic import UUID4


class Session(BaseModel):
    user_id: UUID4
    access_token: str
    refresh_token: str

    class Config:
        orm_mode = True
