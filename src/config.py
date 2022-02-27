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

    MAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int

    MAIL_VERIFICATION_COOLDOWN_MINUTES: int
    PASSWORD_RESET_COOLDOWN_MINUTES: int

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

    IPINFO_ACCESS_TOKEN: str

    SUDO_MODE_TIME_HOURS: int

    class Config:
        env_file = ".env"


settings = Settings()
