# app.core.config.py
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
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_KEY = os.getenv("OPENAI_KEY")


class Settings(BaseSettings):
    env: str = "dev"
    use_test_db: bool = bool(os.getenv("TEST_DATABASE_URL", False))
    database_url: str
    test_database_url: str

    @property
    def sqlalchemy_database_url(self):
        return self.test_database_url if self.use_test_db else self.database_url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

print("DATABASE_URL:", os.getenv("DATABASE_URL"))
settings = Settings()
# class Settings(BaseSettings):
#     database_url: str
#     test_database_url: str
#     secret_key: str
#     api_key: str
#
#     class Config:
#         env_file = ".env"
#
#
# settings = Settings()
