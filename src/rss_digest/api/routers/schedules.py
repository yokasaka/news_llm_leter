"""Schedule endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from rss_digest.api.dependencies import get_current_user, get_repositories
from rss_digest.api.routers.helpers import (
    get_group_or_404,
    get_schedule_or_404,
    schedule_response,
)
from rss_digest.api.schemas import (
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from rss_digest.db.models import GroupSchedule, User
from rss_digest.repository import Repositories
from rss_digest.services.scheduler.service import parse_time_hhmm

router = APIRouter(prefix="/groups/{group_id}/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleResponse])
def list_schedules(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[ScheduleResponse]:
    group = get_group_or_404(repos, group_id, current_user)
    schedules = repos.schedules.list_by_group(group.id)
    return [schedule_response(schedule) for schedule in schedules]


@router.post("", response_model=ScheduleResponse)
def create_schedule(
    group_id: UUID,
    payload: ScheduleCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> ScheduleResponse:
    group = get_group_or_404(repos, group_id, current_user)
    parse_time_hhmm(payload.time_hhmm)
    schedule = GroupSchedule(group_id=group.id, time_hhmm=payload.time_hhmm)
    persisted = repos.schedules.add(schedule)
    return schedule_response(persisted)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    group_id: UUID,
    schedule_id: UUID,
    payload: ScheduleUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> ScheduleResponse:
    group = get_group_or_404(repos, group_id, current_user)
    schedule = get_schedule_or_404(repos, group.id, schedule_id)
    updated_time = payload.time_hhmm or schedule.time_hhmm
    parse_time_hhmm(updated_time)
    updated = GroupSchedule(
        id=schedule.id,
        group_id=schedule.group_id,
        time_hhmm=updated_time,
        enabled=payload.enabled if payload.enabled is not None else schedule.enabled,
        last_fired_at=schedule.last_fired_at,
    )
    persisted = repos.schedules.add(updated)
    return schedule_response(persisted)


@router.delete("/{schedule_id}")
def delete_schedule(
    group_id: UUID,
    schedule_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> dict:
    group = get_group_or_404(repos, group_id, current_user)
    schedule = get_schedule_or_404(repos, group.id, schedule_id)
    repos.schedules.delete(schedule.id)
    return {"status": "deleted"}
