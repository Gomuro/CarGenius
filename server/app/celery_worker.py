import os
from celery import Celery
# from app.core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")

# Automatically detect tasks in 'app' applications
celery.autodiscover_tasks(['app'])
