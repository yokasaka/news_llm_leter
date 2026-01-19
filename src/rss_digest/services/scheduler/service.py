"""Scheduling utilities for group pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from rss_digest.db.models import Group, GroupSchedule, User
from rss_digest.repository import GroupSchedulesRepo, GroupsRepo, UsersRepo


def parse_time_hhmm(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("time_hhmm must be in HH:MM format")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("time_hhmm must be a valid time")
    return hour, minute


def floor_minute(value: datetime) -> datetime:
    return value.replace(second=0, microsecond=0)


def same_minute(left: datetime, right: datetime) -> bool:
    return floor_minute(left) == floor_minute(right)


@dataclass
class DueSchedule:
    schedule: GroupSchedule
    group: Group
    user: User
    scheduled_at: datetime


class SchedulerService:
    def __init__(
        self,
        schedules: GroupSchedulesRepo,
        groups: GroupsRepo,
        users: UsersRepo,
    ) -> None:
        self._schedules = schedules
        self._groups = groups
        self._users = users

    def tick(self, now: datetime) -> list[DueSchedule]:
        now_utc = now.astimezone(timezone.utc)
        due: list[DueSchedule] = []
        for schedule in self._schedules.list_enabled():
            group = self._groups.get(schedule.group_id)
            if group is None or not group.is_enabled:
                continue
            user = self._users.get(group.user_id)
            if user is None:
                continue
            if schedule.last_fired_at and same_minute(
                schedule.last_fired_at, now_utc
            ):
                continue
            tz = ZoneInfo(user.timezone)
            local_time = now_utc.astimezone(tz)
            hour, minute = parse_time_hhmm(schedule.time_hhmm)
            if local_time.hour == hour and local_time.minute == minute:
                scheduled_at = floor_minute(now_utc)
                self._schedules.update_last_fired(schedule.id, scheduled_at)
                due.append(
                    DueSchedule(
                        schedule=schedule,
                        group=group,
                        user=user,
                        scheduled_at=scheduled_at,
                    )
                )
        return due
