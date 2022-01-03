from fastapi_mail import FastMail, ConnectionConfig
from pydantic import EmailStr
from .config import settings
from pathlib import Path


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
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates'
)


async def send_email(email, template_name):
    fm = FastMail(MAIL_CONFIG)
    await fm.send_message(email, template_name)

