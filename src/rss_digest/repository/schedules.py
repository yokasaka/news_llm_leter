"""Schedule repository."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from rss_digest.models import GroupSchedule
from rss_digest.repository.base import InMemoryRepository, RepositoryError


class GroupSchedulesRepo(InMemoryRepository):
    def add(self, record: GroupSchedule) -> None:  # type: ignore[override]
        super().add(record)

    def list_enabled(self) -> list[GroupSchedule]:
        return [schedule for schedule in self.list_all() if schedule.enabled]

    def list_by_group(self, group_id: UUID) -> list[GroupSchedule]:
        return [schedule for schedule in self.list_all() if schedule.group_id == group_id]

    def update_last_fired(self, schedule_id: UUID, fired_at: datetime) -> None:
        schedule = self.get(schedule_id)
        if schedule is None:
            raise RepositoryError("Schedule not found")
        self._records[schedule_id] = replace(schedule, last_fired_at=fired_at)
