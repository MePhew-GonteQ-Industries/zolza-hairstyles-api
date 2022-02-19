import string
import random

from src.config import settings
from ..conf_test import client, session  # noqa
import pytest
from fastapi import status
from faker import Faker
from src.schemas import user

faker = Faker()

ROUTE_PREFIX = "/users/"


@pytest.mark.parametrize(
    "content_language, preferred_theme, gender",
    [("pl", "dark", "male"), ("en", "light", "female"), ("pl", "dark", "other")],
)
def test_create_user(client, content_language, preferred_theme, gender):
    identity = faker.name().split(" ")
    name = identity[0]
    surname = identity[1]
    user_data = {
        "email": faker.email(),
        "name": name,
        "surname": surname,
        "gender": gender,
        "password": "Kwakwa5!",
    }
    res = client.post(
        settings.BASE_URL + ROUTE_PREFIX + "register",
        headers={
            "content-language": content_language,
            "preferred-theme": preferred_theme,
        },
        json=user_data,
    )
    _ = user.ReturnUser(**res.json())
    user_data["permission_level"] = ["user"]
    user_data["verified"] = False
    user_data["settings"] = [
        {
            "current_value": preferred_theme,
            "default_value": None,
            "name": "preferred_theme",
        },
        {"current_value": content_language, "default_value": None, "name": "language"},
    ]
    user_data.pop("password")
    response_body = res.json()
    response_body.pop("created_at")

    assert response_body == user_data
    assert res.status_code == status.HTTP_201_CREATED


def test_request_email_verification(client):
    user_email = {"email": faker.email()}
    res = client.post(
        settings.BASE_URL + ROUTE_PREFIX + "request-email-verification", json=user_email
    )

    assert res.json() == user_email
    assert res.status_code == status.HTTP_202_ACCEPTED


@pytest.mark.parametrize(
    "verification_token, status_code",
    [
        (
            "".join([random.choice(string.ascii_letters) for _ in range(40)]),
            status.HTTP_401_UNAUTHORIZED,
        )
    ],
)
def test_verify_email(client, verification_token, status_code):
    res = client.put(
        settings.BASE_URL + ROUTE_PREFIX + "verify-email",
        json={"verification_token": verification_token},
    )

    assert res.status_code == status_code
