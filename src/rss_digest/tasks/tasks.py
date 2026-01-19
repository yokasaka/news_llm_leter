"""Celery tasks for scheduled processing."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

from rss_digest.models import JobRun
from rss_digest.services.scheduler.service import SchedulerService
from rss_digest.tasks.app import celery_app
from rss_digest.tasks.factory import build_pipeline, build_repositories


@celery_app.task
def tick_due_schedules(now_iso: str | None = None, db_path: str | None = None) -> int:
    repositories = build_repositories(db_path)
    now = datetime.fromisoformat(now_iso) if now_iso else datetime.now(timezone.utc)
    scheduler = SchedulerService(repositories.schedules, repositories.groups, repositories.users)
    due = scheduler.tick(now)
    for schedule in due:
        run_group_pipeline.delay(
            str(schedule.group.id), schedule.scheduled_at.isoformat(), db_path
        )
    return len(due)


@celery_app.task
def run_group_pipeline(
    group_id: str, scheduled_at_iso: str, db_path: str | None = None
) -> str:
    repositories = build_repositories(db_path)
    pipeline = build_pipeline(repositories)
    job = JobRun(
        group_id=UUID(group_id),
        job_type="pipeline",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    repositories.job_runs.add(job)
    try:
        result = pipeline.run(UUID(group_id), datetime.fromisoformat(scheduled_at_iso))
    except Exception as exc:  # noqa: BLE001
        repositories.job_runs.add(
            replace(
                job,
                status="failed",
                finished_at=datetime.now(timezone.utc),
                error_message=str(exc),
            )
        )
        raise
    repositories.job_runs.add(
        replace(job, status="success", finished_at=datetime.now(timezone.utc))
    )
    return str(result.digest.id)
