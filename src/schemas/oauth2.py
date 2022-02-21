from pydantic import BaseModel, Field
from enum import Enum
from pydantic import UUID4


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
