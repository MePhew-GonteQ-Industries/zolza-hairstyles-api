from pydantic import BaseModel


class Session(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str

    class Config:
        orm_mode = True
