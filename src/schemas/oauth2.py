from pydantic import BaseModel, Field
from enum import Enum
from typing import Union


class TokenType(str, Enum):
    access_token = 'access'
    refresh_token = 'refresh'
    email_verification_token = 'email_verification'
    password_reset_token = 'password_reset'


class TokenPayloadBase(BaseModel):
    user_id: int
    token_type: str


class ReturnTokenPayload(TokenPayloadBase):
    expires: str
    issued_at: str


class CreateTokenPayload(TokenPayloadBase):
    permission_level: Union[str, None] = None


class ReturnAccessTokenPayload(BaseModel):
    user_id: int
    permission_level: str
    access_token: str


class ReturnGenericToken(BaseModel):
    user_id: int


class ReturnAccessToken(BaseModel):
    access_token: str
    token_type: str
    scope: str
    expires_in: int = Field(gt=0)
    refresh_token: str
