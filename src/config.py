from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App config
    API_VERSION: str
    API_TITLE: str
    LOG_LEVEL: str = "INFO"

    COMPANY_TIMEZONE: str

    COMPANY_NAME: str
    BASE_URL: str
    FRONTEND_URL: str

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

    # GITHUB config (used for an unrelated proxy, disabled if not set)
    GH_APP_CLIENT_ID: str | None = None
    GH_APP_CLIENT_SECRET: str | None = None
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
