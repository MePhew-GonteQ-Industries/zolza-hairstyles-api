import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.database import Base, get_db
from src.main import app

SQLALCHEMY_TEST_DATABASE_URL = f'postgresql://' \
                          f'{settings.DATABASE_USERNAME}:' \
                          f'{settings.DATABASE_PASSWORD}@' \
                          f'{settings.DATABASE_HOSTNAME}:' \
                          f'{settings.DATABASE_PORT}/' \
                          f'{settings.DATABASE_NAME}_test'

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session):
    def get_test_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = get_test_db

    yield TestClient(app)
