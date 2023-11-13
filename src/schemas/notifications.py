import datetime

from pydantic import ConfigDict, BaseModel


class FcmToken(BaseModel):
    fcm_token: str


class ReturnFcmToken(FcmToken):
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)
