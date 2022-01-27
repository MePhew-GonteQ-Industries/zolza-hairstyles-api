from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password):
    return pwd_context.hash(password)


def compare_passwords(plain_text_password, hashed_password):
    return pwd_context.verify(plain_text_password, hashed_password)


def on_decode_error(*, db, request_db):
    db.delete(request_db)
    db.commit()
