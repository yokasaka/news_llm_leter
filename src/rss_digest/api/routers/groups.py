"""Group endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from rss_digest.api.dependencies import get_current_user, get_repositories
from rss_digest.api.routers.helpers import get_group_or_404, group_response
from rss_digest.api.schemas import GroupCreateRequest, GroupResponse, GroupUpdateRequest
from rss_digest.db.models import Group, User
from rss_digest.repository import Repositories

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupResponse])
def list_groups(
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[GroupResponse]:
    groups = repos.groups.list_by_user(current_user.id)
    return [group_response(group) for group in groups]


@router.post("", response_model=GroupResponse)
def create_group(
    payload: GroupCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> GroupResponse:
    group = Group(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description or "",
        is_enabled=True,
    )
    persisted = repos.groups.add(group)
    return group_response(persisted)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> GroupResponse:
    group = get_group_or_404(repos, group_id, current_user)
    return group_response(group)


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: UUID,
    payload: GroupUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> GroupResponse:
    group = get_group_or_404(repos, group_id, current_user)
    updated = Group(
        id=group.id,
        user_id=group.user_id,
        name=payload.name or group.name,
        description=payload.description or group.description,
        is_enabled=payload.is_enabled if payload.is_enabled is not None else group.is_enabled,
        last_run_started_at=group.last_run_started_at,
        last_run_completed_at=group.last_run_completed_at,
    )
    repos.groups.add(updated)
    return group_response(updated)


@router.delete("/{group_id}")
def delete_group(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> dict:
    group = get_group_or_404(repos, group_id, current_user)
    repos.groups.delete(group.id)
    return {"status": "deleted"}
