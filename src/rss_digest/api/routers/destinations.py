"""Destination endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from rss_digest.api.dependencies import get_current_user, get_repositories
from rss_digest.api.routers.helpers import (
    destination_response,
    get_destination_or_404,
    get_group_or_404,
)
from rss_digest.api.schemas import (
    DestinationCreateRequest,
    DestinationResponse,
    DestinationUpdateRequest,
)
from rss_digest.models import GroupDestination, User
from rss_digest.repository import Repositories

router = APIRouter(prefix="/groups/{group_id}/destinations", tags=["destinations"])


@router.get("", response_model=list[DestinationResponse])
def list_destinations(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[DestinationResponse]:
    group = get_group_or_404(repos, group_id, current_user)
    destinations = repos.destinations.list_by_group(group.id)
    return [destination_response(destination) for destination in destinations]


@router.post("", response_model=DestinationResponse)
def create_destination(
    group_id: UUID,
    payload: DestinationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> DestinationResponse:
    group = get_group_or_404(repos, group_id, current_user)
    destination = GroupDestination(
        group_id=group.id,
        type=payload.type,
        destination=payload.destination,
        token_enc=payload.token,
    )
    repos.destinations.add(destination)
    return destination_response(destination)


@router.patch("/{destination_id}", response_model=DestinationResponse)
def update_destination(
    group_id: UUID,
    destination_id: UUID,
    payload: DestinationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> DestinationResponse:
    group = get_group_or_404(repos, group_id, current_user)
    destination = get_destination_or_404(repos, group.id, destination_id)
    updated = GroupDestination(
        id=destination.id,
        group_id=destination.group_id,
        type=destination.type,
        destination=destination.destination,
        token_enc=destination.token_enc,
        enabled=payload.enabled if payload.enabled is not None else destination.enabled,
    )
    repos.destinations.add(updated)
    return destination_response(updated)


@router.delete("/{destination_id}")
def delete_destination(
    group_id: UUID,
    destination_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> dict:
    group = get_group_or_404(repos, group_id, current_user)
    destination = get_destination_or_404(repos, group.id, destination_id)
    repos.destinations.delete(destination.id)
    return {"status": "deleted"}
