import pytest
from fastapi.testclient import TestClient
from fastapi_mail import FastMail, ConnectionConfig
from pathlib import Path

from pydantic import EmailStr

from src.config import settings
from src.database import get_db
from src.email_manager import get_fastMail_client
from src.main import app
from .conf_database import session # noqa


@pytest.fixture
def client(session):
    def get_test_db():
        try:
            yield session
        finally:
            session.close()

    def get_test_fastMail_client():
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
            TEMPLATE_FOLDER=Path(__file__).parent.parent / "src/templates",
            SUPPRESS_SEND=True
        )
        test_fastMail = FastMail(MAIL_CONFIG)
        return test_fastMail

    app.dependency_overrides[get_fastMail_client] = get_test_fastMail_client
    app.dependency_overrides[get_db] = get_test_db

    yield TestClient(app)
