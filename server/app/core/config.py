from pathlib import Path
from dotenv import load_dotenv
import os
from pydantic import BaseSettings


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
API_KEY = os.getenv("API_KEY")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR /".env"

load_dotenv(dotenv_path=ENV_PATH)


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
