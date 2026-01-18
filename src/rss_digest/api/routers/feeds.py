"""Feed endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends

from rss_digest.api.dependencies import get_current_user, get_repositories
from rss_digest.api.routers.helpers import (
    get_group_feed_or_404,
    get_group_or_404,
    group_feed_response,
    group_feed_responses,
)
from rss_digest.api.schemas import (
    FeedAddRequest,
    FeedCandidateResponse,
    FeedDiscoverRequest,
    GroupFeedResponse,
    GroupFeedUpdateRequest,
)
from rss_digest.models import GroupFeed, User
from rss_digest.repository import Repositories
from rss_digest.services.rss.discovery import RssDiscoveryService

router = APIRouter(prefix="/groups/{group_id}/feeds", tags=["feeds"])


@router.get("", response_model=list[GroupFeedResponse])
def list_feeds(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[GroupFeedResponse]:
    group = get_group_or_404(repos, group_id, current_user)
    return group_feed_responses(repos, group.id)


@router.post(":add_by_feed_url", response_model=GroupFeedResponse)
def add_feed(
    group_id: UUID,
    payload: FeedAddRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> GroupFeedResponse:
    group = get_group_or_404(repos, group_id, current_user)
    feed_source = repos.feed_sources.find_by_url(payload.feed_url)
    if feed_source is None:
        feed_source = _build_feed_source(payload.feed_url)
        repos.feed_sources.add(feed_source)
    group_feed = GroupFeed(group_id=group.id, feed_source_id=feed_source.id)
    repos.group_feeds.add(group_feed)
    return group_feed_response(group_feed, feed_source.url)


@router.post(":discover_by_site_url", response_model=list[FeedCandidateResponse])
def discover_feed(
    group_id: UUID,
    payload: FeedDiscoverRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[FeedCandidateResponse]:
    _ = group_id
    _ = current_user
    service = RssDiscoveryService()
    response = httpx.get(payload.site_url, timeout=10)
    response.raise_for_status()
    candidates = service.discover(payload.site_url, response.text)
    return [
        FeedCandidateResponse(url=candidate.url, type=candidate.type, title=candidate.title)
        for candidate in candidates
    ]


@router.patch("/{group_feed_id}", response_model=GroupFeedResponse)
def update_feed(
    group_id: UUID,
    group_feed_id: UUID,
    payload: GroupFeedUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> GroupFeedResponse:
    group = get_group_or_404(repos, group_id, current_user)
    group_feed = get_group_feed_or_404(repos, group.id, group_feed_id)
    updated = GroupFeed(
        id=group_feed.id,
        group_id=group_feed.group_id,
        feed_source_id=group_feed.feed_source_id,
        enabled=payload.enabled,
    )
    repos.group_feeds.add(updated)
    feed_source = repos.feed_sources.get(updated.feed_source_id)
    return group_feed_response(updated, feed_source.url if feed_source else "")


@router.delete("/{group_feed_id}")
def delete_feed(
    group_id: UUID,
    group_feed_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> dict:
    group = get_group_or_404(repos, group_id, current_user)
    group_feed = get_group_feed_or_404(repos, group.id, group_feed_id)
    repos.group_feeds.delete(group_feed.id)
    return {"status": "deleted"}


def _build_feed_source(url: str):
    from rss_digest.models import FeedSource

    return FeedSource(url=url)
