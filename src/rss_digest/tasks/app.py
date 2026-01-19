"""Celery application configuration."""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab


def create_celery_app() -> Celery:
    app = Celery("rss_digest")
    app.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    app.conf.beat_schedule = {
        "tick-due-schedules": {
            "task": "rss_digest.tasks.tasks.tick_due_schedules",
            "schedule": crontab(minute="*"),
        }
    }
    if os.getenv("CELERY_TASK_ALWAYS_EAGER", "").lower() in {"1", "true", "yes"}:
        app.conf.task_always_eager = True
    return app


celery_app = create_celery_app()
