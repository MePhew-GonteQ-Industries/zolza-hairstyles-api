from pydantic import BaseModel


class FcmToken(BaseModel):
    fcm_token: str
