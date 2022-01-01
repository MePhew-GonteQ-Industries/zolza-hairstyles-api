from pydantic import BaseModel


class BaseUserSettings(BaseModel):
    language: str
    prefered_theme: str

    class Config:
        orm_mode = True
