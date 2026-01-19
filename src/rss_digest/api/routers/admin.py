"""Admin endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from rss_digest.api.dependencies import get_repositories, require_admin
from rss_digest.api.routers.helpers import user_response
from rss_digest.api.schemas import (
    AdminFeedHealthResponse,
    AdminMetricsResponse,
    AdminUsageResponse,
    DeliveryResponse,
    JobRunResponse,
    UserResponse,
)
from rss_digest.models import User
from rss_digest.repository import Repositories

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
def admin_users(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[UserResponse]:
    return [user_response(user) for user in repos.users.list_all()]


@router.get("/feeds", response_model=list[AdminFeedHealthResponse])
def admin_feeds(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[AdminFeedHealthResponse]:
    return [
        AdminFeedHealthResponse(
            id=feed_source.id,
            url=feed_source.url,
            health_status=feed_source.health_status,
            consecutive_failures=feed_source.consecutive_failures,
            last_fetch_at=feed_source.last_fetch_at,
        )
        for feed_source in repos.feed_sources.list_all()
    ]


@router.get("/jobs", response_model=list[JobRunResponse])
def admin_jobs(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[JobRunResponse]:
    return [
        JobRunResponse(
            id=job.id,
            group_id=job.group_id,
            job_type=job.job_type,
            status=job.status,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_message=job.error_message,
        )
        for job in repos.job_runs.list_all()
    ]


@router.get("/deliveries", response_model=list[DeliveryResponse])
def admin_deliveries(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[DeliveryResponse]:
    return [
        DeliveryResponse(
            id=delivery.id,
            digest_id=delivery.digest_id,
            destination_id=delivery.destination_id,
            status=delivery.status,
            error_message=delivery.error_message,
        )
        for delivery in repos.deliveries.list_all()
    ]


@router.get("/usage", response_model=AdminUsageResponse)
def admin_usage(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> AdminUsageResponse:
    return AdminUsageResponse(
        total_users=len(repos.users.list_all()),
        total_groups=len(repos.groups.list_all()),
        total_feed_sources=len(repos.feed_sources.list_all()),
        total_group_feeds=len(repos.group_feeds.list_all()),
        total_digests=len(repos.digests.list_all()),
        total_deliveries=len(repos.deliveries.list_all()),
    )


@router.get("/metrics", response_model=AdminMetricsResponse)
def admin_metrics(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> AdminMetricsResponse:
    digests = repos.digests.list_all()
    deliveries = repos.deliveries.list_all()
    now = datetime.now(timezone.utc)
    recent_digests = [
        digest
        for digest in digests
        if digest.scheduled_at and digest.scheduled_at >= now - timedelta(days=7)
    ]
    active_group_ids = {
        digest.group_id
        for digest in recent_digests
        if any(
            delivery.digest_id == digest.id and delivery.status == "sent"
            for delivery in deliveries
        )
    }
    active_users = {
        group.user_id
        for group in repos.groups.list_all()
        if group.id in active_group_ids
    }
    feed_sources = repos.feed_sources.list_all()
    total_fetches = sum(source.fetch_count for source in feed_sources)
    total_not_modified = sum(source.not_modified_count for source in feed_sources)
    total_failures = sum(source.failure_count for source in feed_sources)
    delivery_total = len(deliveries)
    failed_deliveries = len([delivery for delivery in deliveries if delivery.status != "sent"])
    return AdminMetricsResponse(
        active_users=len([user_id for user_id in active_users if user_id is not None]),
        feed_not_modified_rate=_safe_rate(total_not_modified, total_fetches),
        feed_failure_rate=_safe_rate(total_failures, total_fetches),
        llm_evaluations=len(repos.evaluations.list_all()),
        llm_summaries=len(repos.summaries.list_all()),
        delivery_failure_rate=_safe_rate(failed_deliveries, delivery_total),
    )


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
