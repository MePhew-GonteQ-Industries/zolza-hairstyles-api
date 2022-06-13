import datetime

from pydantic import BaseModel


class FcmToken(BaseModel):
    fcm_token: str


class ReturnFcmToken(FcmToken):
    updated_at: datetime.datetime

    class Config:
        orm_mode = True
