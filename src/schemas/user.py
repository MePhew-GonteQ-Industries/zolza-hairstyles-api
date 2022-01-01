from enum import Enum
from pydantic import BaseModel, EmailStr


class Gender(str, Enum):
    male = "male"
    female = "female"


class BaseUser(BaseModel):
    email: EmailStr
    name: str
    surname: str
    gender: Gender

    class Config:
        orm_mode = True


class CreateUser(BaseUser):
    password: str
