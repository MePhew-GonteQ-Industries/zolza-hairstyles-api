from pydantic import BaseSettings, EmailStr


class Settings(BaseSettings):
    API_VERSION: str
    API_TITLE: str
    BASE_URL: str
    ZOLZA_HAIRSTYLES_URL: str

    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str
    DATABASE_HOSTNAME: str
    DATABASE_PORT: str
    DATABASE_NAME: str

    API_SECRET: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_TLS: bool
    MAIL_SSL: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool
    MAIL_FROM_NAME: str

    class Config:
        env_file = ".env"


settings = Settings()
