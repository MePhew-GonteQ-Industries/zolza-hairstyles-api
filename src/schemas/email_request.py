from enum import Enum
from pydantic import BaseModel, Field, validator
import re


class EmailRequestType(str, Enum):
    email_verification_request = 'email_verification_request'
    password_reset_request = 'password_reset_request'


class EmailRequest(BaseModel):
    user_id: int
    request_type: EmailRequestType
    request_token: str

    class Config:
        orm_mode = True


class EmailVerificationRequest(BaseModel):
    verification_token: str


class PasswordResetRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8, max_length=200)

    @validator('new_password')
    def verify_strong_password(cls, v):
        strong_password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$"

        if re.fullmatch(strong_password_regex, v):
            return v
        else:
            raise ValueError('ensure the new password is strong')
