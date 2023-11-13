import re
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import field_validator, ConfigDict, BaseModel, EmailStr, Field, UUID4

from .user_settings import ReturnSetting


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class UserEmailOnly(BaseModel):
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserData(BaseModel):
    name: str = Field(max_length=50)
    surname: str = Field(max_length=50)
    gender: Gender


class BaseUser(UserEmailOnly, UserData):
    pass


class CreateUser(BaseUser):
    password: str = Field(min_length=8, max_length=200)

    @field_validator("password")
    @classmethod
    def verify_strong_password(cls, v):
        strong_password_regex = (
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$"
        )

        if re.fullmatch(strong_password_regex, v):
            return v
        else:
            raise ValueError("ensure the password is strong")


class ReturnUser(BaseUser):
    permission_level: List[str]
    verified: bool
    created_at: datetime


class ReturnUserDetailed(ReturnUser):
    id: UUID4
    disabled: bool


class ReturnUsers(BaseModel):
    users: List[ReturnUserDetailed]


class ReturnUserAndSettings(ReturnUser):
    settings: List[ReturnSetting]
