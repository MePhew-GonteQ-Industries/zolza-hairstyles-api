from typing import Optional

from fastapi import HTTPException, status

from src.config import settings


class UserNotFoundException(HTTPException):
    def __init__(self):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = "Could not validate credentials"


class AdditionalAuthenticationRequiredHTTPException(HTTPException):
    def __init__(
        self,
        detail: str = f"Additional authentication required; "
        f"Authenticate using {settings.FRONTEND_URL}"
        f"{settings.BASE_URL}/auth/enter-sudo-mode",
    ):
        self.status_code = status.HTTP_403_FORBIDDEN
        self.detail = detail


class ResourceNotFoundHTTPException(HTTPException):
    def __init__(
        self, *, detail: str = "Requested resource was not found on the server"
    ):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = detail


class IncorrectTokenDataException(Exception):
    pass


class InvalidTokenHTTPException(HTTPException):
    def __init__(
        self,
        detail: str = "Invalid or expired verification code provided",
        status_code: status = status.HTTP_401_UNAUTHORIZED,
        headers: Optional[dict] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        if headers:
            self.headers = headers


class AccountDisabledHTTPException(HTTPException):
    def __init__(self):
        self.detail = "This account has been suspended"
        self.status_code = status.HTTP_403_FORBIDDEN
        self.headers = {"WWW-Authenticate": "Bearer"}


class UnverifiedUserHTTPException(HTTPException):
    def __init__(self):
        self.detail = "User is not verified"
        self.status_code = status.HTTP_403_FORBIDDEN
        self.headers = {"WWW-Authenticate": "Bearer"}


class InsufficientPermissionsHTTPException(HTTPException):
    def __init__(self):
        self.detail = "Insufficient permissions to perform this action"
        self.status_code = status.HTTP_403_FORBIDDEN
        self.headers = {"WWW-Authenticate": "Bearer"}


class InvalidEnumerationMemberHTTPException(HTTPException):
    def __init__(self):
        self.detail = [
            {
                "loc": ["header", "content-language"],
                "msg": "value is not a valid enumeration member; permitted: 'pl', 'en'",
                "type": "type_error.enum",
                "ctx": {"enum_values": ["pl", "en"]},
            }
        ]
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class CooldownHTTPException(HTTPException):
    def __init__(self, cooldown_left: str, *, detail: str):
        self.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        self.detail = detail
        self.headers = {"Retry-After": str(cooldown_left)}


class InvalidApiKeyHTTPException(HTTPException):
    def __init__(self):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = "Could not validate credentials"
        self.headers = {"WWW-Authenticate": "x-api_key"}


class InvalidGrantTypeHTTPException(HTTPException):
    def __init__(self, grant_type):
        self.detail = [
            {
                "loc": ["body", "grant_type"],
                "msg": f'grant_type needs to match "{grant_type}"',
                "type": "value_error.str",
                "ctx": {"pattern": f"{grant_type}"},
            }
        ]
        self.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class SessionNotFoundHTTPException(HTTPException):
    def __init__(self):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = "Provided token is bound to an invalidated session"
