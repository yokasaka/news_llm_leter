"""Admin endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from rss_digest.api.dependencies import get_repositories, require_admin
from rss_digest.api.routers.helpers import group_feed_response, user_response
from rss_digest.api.schemas import DeliveryResponse, GroupFeedResponse, UserResponse
from rss_digest.models import User
from rss_digest.repository import Repositories

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
def admin_users(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[UserResponse]:
    return [user_response(user) for user in repos.users.list_all()]


@router.get("/feeds", response_model=list[GroupFeedResponse])
def admin_feeds(
    _: Annotated[User, Depends(require_admin)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[GroupFeedResponse]:
    responses: list[GroupFeedResponse] = []
    for group_feed in repos.group_feeds.list_all():
        feed_source = repos.feed_sources.get(group_feed.feed_source_id)
        responses.append(
            group_feed_response(group_feed, feed_source.url if feed_source else "")
        )
    return responses


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
