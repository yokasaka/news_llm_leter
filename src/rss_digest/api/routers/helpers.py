"""Shared helpers for API routers."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status

from rss_digest.api.schemas import (
    DestinationResponse,
    DigestResponse,
    GroupFeedResponse,
    GroupResponse,
    ScheduleResponse,
    UserResponse,
)
from rss_digest.db.models import Group, GroupDestination, GroupFeed, GroupSchedule, User
from rss_digest.repository import Repositories


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
        timezone=user.timezone,
    )


def group_response(group: Group) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        is_enabled=group.is_enabled,
        last_run_started_at=group.last_run_started_at,
        last_run_completed_at=group.last_run_completed_at,
    )


def group_feed_response(group_feed: GroupFeed, feed_url: str) -> GroupFeedResponse:
    return GroupFeedResponse(
        id=group_feed.id,
        feed_source_id=group_feed.feed_source_id,
        feed_url=feed_url,
        enabled=group_feed.enabled,
    )


def group_feed_responses(repos: Repositories, group_id: UUID) -> list[GroupFeedResponse]:
    responses: list[GroupFeedResponse] = []
    for group_feed in repos.group_feeds.list_by_group(group_id):
        feed_source = repos.feed_sources.get(group_feed.feed_source_id)
        responses.append(
            group_feed_response(group_feed, feed_source.url if feed_source else "")
        )
    return responses


def schedule_response(schedule: GroupSchedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id,
        time_hhmm=schedule.time_hhmm,
        enabled=schedule.enabled,
        last_fired_at=schedule.last_fired_at,
    )


def destination_response(destination: GroupDestination) -> DestinationResponse:
    return DestinationResponse(
        id=destination.id,
        type=destination.type,
        destination=destination.destination,
        enabled=destination.enabled,
    )


def digest_response(digest) -> DigestResponse:
    return DigestResponse(
        id=digest.id,
        scheduled_at=digest.scheduled_at,
        markdown_body=digest.markdown_body,
        storage_path=digest.storage_path,
    )


def get_group_or_404(repos: Repositories, group_id: UUID, user: User) -> Group:
    group = repos.groups.get(group_id)
    if group is None or group.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


def get_group_feed_or_404(
    repos: Repositories, group_id: UUID, group_feed_id: UUID
) -> GroupFeed:
    group_feed = repos.group_feeds.get(group_feed_id)
    if group_feed is None or group_feed.group_id != group_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feed not found")
    return group_feed


def get_schedule_or_404(
    repos: Repositories, group_id: UUID, schedule_id: UUID
) -> GroupSchedule:
    schedule = repos.schedules.get(schedule_id)
    if schedule is None or schedule.group_id != group_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return schedule


def get_destination_or_404(
    repos: Repositories, group_id: UUID, destination_id: UUID
) -> GroupDestination:
    destination = repos.destinations.get(destination_id)
    if destination is None or destination.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found"
        )
    return destination
