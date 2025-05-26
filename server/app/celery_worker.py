# app/celery_worker.py
import os
from celery import Celery
from app.core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from app.celery_beat_schedule import CELERY_BEAT_SCHEDULE

celery = Celery(__name__,
broker = CELERY_BROKER_URL,
backend = CELERY_RESULT_BACKEND
)

celery.conf.beat_schedule = CELERY_BEAT_SCHEDULE
celery.conf.timezone = 'UTC'  # Set the timezone for Celery tasks

# Automatically detect tasks in 'app' applications
celery.autodiscover_tasks(['app'])
