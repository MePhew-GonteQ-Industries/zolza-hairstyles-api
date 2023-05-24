from pydantic import BaseSettings, EmailStr


class Settings(BaseSettings):
    # App config
    API_VERSION: str
    API_TITLE: str
    BASE_URL: str
    ZOLZA_HAIRSTYLES_URL: str
    LOG_LEVEL: str = 'INFO'

    API_SECRET: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int

    MAIL_VERIFICATION_COOLDOWN_MINUTES: int
    PASSWORD_RESET_COOLDOWN_MINUTES: int

    SUDO_MODE_TIME_HOURS: int
    APPOINTMENT_SLOT_TIME_MINUTES: int
    MAX_FUTURE_APPOINTMENT_DAYS: int

    # Database config
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str
    DATABASE_HOSTNAME: str
    DATABASE_PORT: str
    DATABASE_NAME: str

    # Mail config
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool
    MAIL_FROM_NAME: str

    # IPINFO config
    IPINFO_ACCESS_TOKEN: str

    # FIREBASE config
    FIREBASE_SERVICE_ACCOUNT_CREDENTIALS_PATH: str

    # GITHUB config
    GH_APP_CLIENT_ID: str
    GH_APP_CLIENT_SECRET: str

    class Config:
        env_file = ".env"


settings = Settings()
