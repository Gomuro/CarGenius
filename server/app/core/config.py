# app.core.config.py
from pathlib import Path
from dotenv import load_dotenv
import os
from pydantic import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR /".env"
load_dotenv(dotenv_path=ENV_PATH)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
API_KEY = os.getenv("API_KEY")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")   # The URL to the message broker through which Celery receives tasks
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")   # The URL to the backend where Celery stores task results
DATABASE_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("test_database_url")
OPENAI_KEY = os.getenv("OPENAI_KEY")
USE_TEST_DB = os.getenv("USE_TEST_DB", "0")


class Settings(BaseSettings):
    """
    Application configuration class.

    Loads environment variables from a .env file and provides
    access to key configuration values including:

    - Environment type (e.g., 'dev', 'prod')
    - Database URLs (regular and test)
    - Celery broker and result backend URLs
    - Automatically switches between test and production database
      based on USE_TEST_DB flag.
    """
    env: str = "dev"
    use_test_db: bool = bool(int(USE_TEST_DB))
    database_url: str = DATABASE_URL
    test_database_url: str = TEST_DATABASE_URL
    CELERY_BROKER_URL: str = CELERY_BROKER_URL
    CELERY_RESULT_BACKEND: str = CELERY_RESULT_BACKEND

    @property
    def sqlalchemy_database_url(self):
        return self.test_database_url if self.use_test_db else self.database_url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
