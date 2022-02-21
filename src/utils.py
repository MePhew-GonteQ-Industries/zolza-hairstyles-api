from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import UUID4
from sqlalchemy.orm import Session

from src import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def compare_passwords(plain_text_password, hashed_password):
    return pwd_context.verify(plain_text_password, hashed_password)


def on_decode_error(*, db, request_db):
    db.delete(request_db)
    db.commit()


def get_user_from_db(*, uuid: UUID4, db: Session):
    user = db.query(models.User).where(models.User.id == uuid).first()

    if not user:
        raise HTTPException(
            detail=f"User with uuid of {uuid} does not exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return user
