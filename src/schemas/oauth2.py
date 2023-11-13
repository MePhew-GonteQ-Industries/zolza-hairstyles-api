import re
from datetime import datetime

from pydantic import field_validator, ConfigDict, BaseModel, Field
from enum import Enum
from pydantic import UUID4
from src import models
from . import session


class TokenType(str, Enum):
    access_token = "access"
    refresh_token = "refresh"
    email_verification_token = "email_verification"
    password_reset_token = "password_reset"


class TokenPayloadBase(BaseModel):
    user_id: UUID4
    token_type: str


class ReturnTokenPayload(TokenPayloadBase):
    expires: str
    issued_at: str


class ReturnAccessTokenPayload(BaseModel):
    user_id: UUID4
    access_token: str


class ReturnGenericToken(BaseModel):
    user_id: UUID4


class ReturnAccessToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int = Field(gt=0)
    refresh_token: str
    session: session.ActiveUserSession


class PasswordChangeForm(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=200)

    @field_validator("new_password")
    @classmethod
    def verify_strong_password(cls, v):
        strong_password_regex = (
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$"
        )

        if re.fullmatch(strong_password_regex, v):
            return v
        else:
            raise ValueError("ensure the password is strong")


class SudoModeInfo(BaseModel):
    sudo_mode_activated: datetime
    sudo_mode_expires: datetime


class BaseUserSession(BaseModel):
    session: models.Session
    model_config = ConfigDict(arbitrary_types_allowed=True)


class UserSession(BaseUserSession):
    user: models.User


class VerifiedUserSession(BaseUserSession):
    verified_user: models.User


class AdminSession(BaseUserSession):
    admin: models.User


class SuperuserSession(BaseUserSession):
    superuser: models.User
