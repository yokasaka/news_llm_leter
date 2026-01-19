"""Celery tasks for schedule ticking."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from rss_digest.db.session import build_session_factory
from rss_digest.repository import Repositories
from rss_digest.services.digest.builder import DigestBuilder
from rss_digest.services.digest.delivery import DeliveryService
from rss_digest.services.digest.storage import StorageService
from rss_digest.services.evaluation.relevance import KeywordRelevanceEvaluator
from rss_digest.services.evaluation.service import EvaluationService
from rss_digest.services.evaluation.summarizer import SimpleSummarizer
from rss_digest.services.materialize.service import MaterializeService
from rss_digest.services.pipeline.service import GroupPipeline
from rss_digest.services.rss.fetcher import RssFetcher
from rss_digest.services.rss.http_client import fetch_feed
from rss_digest.services.scheduler.celery_app import app
from rss_digest.services.scheduler.service import SchedulerService


def _storage_dir() -> Path:
    return Path(os.getenv("DIGEST_STORAGE_DIR", "./data/digests"))


def _build_pipeline(repositories: Repositories) -> GroupPipeline:
    fetcher = RssFetcher(repositories.feed_sources, repositories.feed_items, fetch_feed)
    materializer = MaterializeService(repositories.items, repositories.group_items)
    evaluator = EvaluationService(
        repositories.items,
        repositories.group_items,
        repositories.evaluations,
        repositories.summaries,
        KeywordRelevanceEvaluator(),
        SimpleSummarizer(),
    )
    builder = DigestBuilder()
    storage = StorageService(_storage_dir())
    delivery = DeliveryService(repositories.deliveries)
    return GroupPipeline(
        repositories,
        fetcher,
        materializer,
        evaluator,
        builder,
        storage,
        delivery,
    )


@app.task(name="rss_digest.services.scheduler.tasks.tick_due_schedules")
def tick_due_schedules() -> int:
    session_factory = build_session_factory()
    session = session_factory()
    try:
        repositories = Repositories.build(session=session)
        scheduler = SchedulerService(
            repositories.schedules,
            repositories.groups,
            repositories.users,
        )
        due = scheduler.tick(datetime.now(timezone.utc))
        if not due:
            return 0
        pipeline = _build_pipeline(repositories)
        for schedule in due:
            pipeline.run(schedule.group.id, schedule.scheduled_at)
        return len(due)
    finally:
        session.close()
