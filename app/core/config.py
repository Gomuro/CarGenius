from dotenv import load_dotenv
import os
from pydantic import BaseSettings

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
API_KEY = os.getenv("API_KEY")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
