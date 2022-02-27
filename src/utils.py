from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import UUID4
from sqlalchemy.orm import Session

from src import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(*,
                    password,
                    user_id,
                    db):
    current_password_hash = (
        db.query(models.Password.password_hash)
        .where(models.Password.user_id == user_id)
        .where(models.Password.current == True)
        .first()
    )

    if not compare_passwords(password, *current_password_hash):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="invalid credentials"
        )


def change_password(*, new_password,
                    user_id,
                    db: Session) -> None:
    recent_passwords = (
        db.query(models.Password)
        .where(models.Password.user_id == user_id)
        .all()
    )

    for recent_password in recent_passwords:
        if compare_passwords(
            new_password, recent_password.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="new password cannot be the same as any of the last 5 passwords",
            )

    old_passwords = (
        db.query(models.Password)
        .where(models.Password.user_id == user_id)
        .where(models.Password.current == False)
        .order_by(models.Password.created_at.desc())
        .offset(4)
        .all()
    )

    for old_password in old_passwords:
        db.delete(old_password)

    db.commit()

    current_password = (
        db.query(models.Password)
        .where(models.Password.user_id == user_id)
        .where(models.Password.current)
        .first()
    )

    current_password.current = False

    db.commit()

    new_password = models.Password(
        password_hash=hash_password(new_password),
        user_id=user_id,
        current=True,
    )

    db.add(new_password)

    db.commit()


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
