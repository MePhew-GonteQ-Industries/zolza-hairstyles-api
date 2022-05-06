import logging
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from . import models, oauth2
from .config import settings
from .exceptions import InvalidEnumerationMemberHTTPException
from .schemas.email_request import EmailRequest, EmailRequestType
from .schemas.oauth2 import TokenPayloadBase, TokenType
from .schemas.user_settings import DefaultContentLanguages

MAIL_CONFIG = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=EmailStr(settings.MAIL_FROM),
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_TLS=settings.MAIL_TLS,
    MAIL_SSL=settings.MAIL_SSL,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)

fastMail = FastMail(MAIL_CONFIG)


def get_fast_mail_client():
    return fastMail


async def send_email(
    email: MessageSchema, template_name: str, fast_mail_client: FastMail
):
    try:
        await fast_mail_client.send_message(email, template_name)
    except ConnectionErrors:
        logging.error("Failed to send message")  # todo: update logs
        raise


def create_email_verification_email(
    content_language: DefaultContentLanguages, user, email_verification_token
):
    match content_language:
        case DefaultContentLanguages.polish:
            template_name = "account_verification_pl.html"
            subject = "Zołza Hairstyles - weryfikacja konta"
        case DefaultContentLanguages.english:
            template_name = "account_verification_en.html"
            subject = "Zołza Hairstyles - account verification"
        case _:
            raise InvalidEnumerationMemberHTTPException()

    message = MessageSchema(
        subject=subject,
        recipients=[user.email],
        template_body={
            "user": user.name,
            "zolza_hairstyles_link": settings.ZOLZA_HAIRSTYLES_URL,
            "account_confirmation_link": f"{settings.ZOLZA_HAIRSTYLES_URL}"
                                         f"/email-verification"
            f"?token={email_verification_token}",
        },
        subtype="html",
    )

    return message, template_name


def create_password_reset_email(
    content_language: DefaultContentLanguages, user, password_reset_token
):
    match content_language:
        case DefaultContentLanguages.polish:
            template_name = "password_reset_pl.html"
            subject = "Zołza Hairstyles - resetowanie hasła"
        case DefaultContentLanguages.english:
            template_name = "password_reset_en.html"
            subject = "Zołza Hairstyles - password reset"
        case _:
            raise InvalidEnumerationMemberHTTPException()

    message = MessageSchema(
        subject=subject,
        recipients=[user.email],
        template_body={
            "user": user.name,
            "password_reset_link": f"https://mephew.ddns.net/password-reset?token={password_reset_token}",
        },
        subtype="html",
    )

    return message, template_name


def create_email_request(
    *, user, token_type: TokenType, request_type: EmailRequestType
):
    token_data = TokenPayloadBase(user_id=user.id, token_type=token_type)
    request_token = oauth2.create_jwt(token_data)

    email_request = EmailRequest(
        user_id=user.id, request_type=request_type, request_token=request_token
    )

    email_request = models.EmailRequests(**email_request.dict())

    return email_request
