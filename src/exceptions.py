from typing import Optional

from fastapi import HTTPException, status
from datetime import timedelta


class IncorrectTokenDataException(Exception):
    pass


class InvalidTokenException(HTTPException):
    def __init__(self,
                 detail: str = 'Invalid or expired verification code provided',
                 status_code: status = status.HTTP_401_UNAUTHORIZED,
                 headers: Optional[dict] = None):
        self.detail = detail
        self.status_code = status_code
        if headers:
            self.headers = headers


class AccountDisabledHTTPException(HTTPException):
    def __init__(self):
        self.detail = 'This account has been suspended'
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.headers = {"WWW-Authenticate": "Bearer"}


class UnverifiedUserHTTPException(HTTPException):
    def __init__(self):
        self.detail = 'User is not verfied'
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.headers = {"WWW-Authenticate": "Bearer"}


class InsufficientPermissionHTTPException(HTTPException):
    def __init__(self):
        self.detail = 'User does not have required permissions to perfrom this action'
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.headers = {"WWW-Authenticate": "Bearer"}


class MalformedAccessTokenException(HTTPException):
    def __init__(self, detail,
                 status_code: status = status.HTTP_401_UNAUTHORIZED,
                 headers: Optional[dict] = None):
        self.detail = detail
        self.status_code = status_code
        if headers:
            self.headers = headers


class InvalidEnumerationMemberHTTPException(HTTPException):
    def __init__(self):
        self.detail = [
            {
                "loc": [
                    "header",
                    "content-language"
                ],
                "msg": "value is not a valid enumeration member; permitted: 'pl', 'en'",
                "type": "type_error.enum",
                "ctx": {
                    "enum_values": [
                        "pl",
                        "en"
                    ]
                }
            }
        ]
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class CooldownHTTPException(HTTPException):
    def __init__(self, cooldown_left: timedelta, *, detail: str):
        self.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        self.detail = detail
        self.headers = {"Retry-After": str(cooldown_left)}


class InvalidApiKeyException(HTTPException):
    def __init__(self):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = "Could not validate credentials"
        self.headers = {"WWW-Authenticate": "x-api_key"}


class InvalidGrantTypeException(HTTPException):
    def __init__(self, grant_type):
        self.detail = [
            {
                "loc": [
                    "body",
                    "grant_type"
                ],
                "msg": f'grant_type needs to match "{grant_type}"',
                "type": "value_error.str",
                "ctx": {
                    "pattern": f"{grant_type}"
                }
            }
        ]
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class SessionNotFoundHTTPException(HTTPException):
    def __init__(self):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = 'Provided token is bound to an invalidated session'
