import pytest
from fastapi.testclient import TestClient

from src.database import Base, SQLALCHEMY_DATABASE_URL, get_db, get_db_engine, \
    get_session
from src.main import app

SQLALCHEMY_TEST_DATABASE_URL = f'{SQLALCHEMY_DATABASE_URL}_test'


database_engine = get_db_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = get_session(database_engine)


@pytest.fixture
def session():
    Base.metadata.drop_all(bind=database_engine)
    Base.metadata.create_all(bind=database_engine)
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
