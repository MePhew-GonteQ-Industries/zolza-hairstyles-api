from pydantic import BaseModel


class UserSettings(BaseModel):
    language: str
    prefered_theme: str
