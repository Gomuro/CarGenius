# app/celery_beat_schedule.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "run_parser_every_30_minutes": {
        "task": "app.tasks.parser_task",
        "schedule": crontab(minute="*/30"),
    },
}
