"""Celery application configuration."""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab


def _broker_url() -> str:
    return os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")


def _backend_url() -> str | None:
    return os.getenv("CELERY_RESULT_BACKEND")


app = Celery("rss_digest", broker=_broker_url(), backend=_backend_url())
app.conf.timezone = "UTC"
app.conf.beat_schedule = {
    "tick_due_schedules": {
        "task": "rss_digest.services.scheduler.tasks.tick_due_schedules",
        "schedule": crontab(minute="*"),
    }
}
