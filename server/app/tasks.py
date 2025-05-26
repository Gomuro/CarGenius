# app/tasks.py
from celery import shared_task
from app.core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
import logging


logger = logging.getLogger("celery")

@shared_task
def parser_task():
    logger.info("Parser task started")
    ### ... ###

    return "Parser task completed"
