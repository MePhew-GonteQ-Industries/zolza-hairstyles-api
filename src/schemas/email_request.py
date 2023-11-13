import re
from enum import Enum

from pydantic import field_validator, ConfigDict, BaseModel, Field, UUID4


class EmailRequestType(str, Enum):
    email_verification_request = "email_verification_request"
    password_reset_request = "password_reset_request"


class EmailRequest(BaseModel):
    user_id: UUID4
    request_type: EmailRequestType
    request_token: str
    model_config = ConfigDict(from_attributes=True)


class EmailVerificationRequest(BaseModel):
    verification_token: str


class PasswordResetRequest(BaseModel):
    reset_token: str
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
            raise ValueError("ensure the new password is strong")
