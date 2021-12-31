from pydantic import BaseSettings
import dotenv
import os

dotenv.load_dotenv()


class Settings(BaseSettings):
    BASE_URL: str = os.getenv('BASE_URL')


settings = Settings()
