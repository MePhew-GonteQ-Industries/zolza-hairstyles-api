from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
from sqlalchemy import engine

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://"
    f"{settings.DATABASE_USERNAME}:"
    f"{settings.DATABASE_PASSWORD}@"
    f"{settings.DATABASE_HOSTNAME}:"
    f"{settings.DATABASE_PORT}/"
    f"{settings.DATABASE_NAME}"
)


def get_db_engine(database_url: str):
    db_engine = create_engine(
        database_url,
        connect_args={"options": "-c statement_timeout=1000"},
        pool_pre_ping=True,
    )
    return db_engine


def get_session(db_engine: engine):
    session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    return session


Base = declarative_base()

database_engine = get_db_engine(SQLALCHEMY_DATABASE_URL)
sessionLocal = get_session(database_engine)


def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
