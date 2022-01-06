from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr
from .user_settings import ReturnSettings
from typing import List


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = 'other'


class BaseUser(BaseModel):
    email: EmailStr
    name: str
    surname: str
    gender: Gender

    class Config:
        orm_mode = True


class CreateUser(BaseUser):
    password: str


class ReturnUser(BaseUser):
    permission_level: list[str]
    verified: bool
    created_at: datetime


class ReturnUserAndSettings(BaseModel):
    user: ReturnUser
    settings: List[ReturnSettings]

    class Config:
        orm_mode = True
