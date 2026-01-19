"""Schedule repository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from rss_digest.db.models import GroupSchedule
from rss_digest.repository.base import ensure_id


class GroupSchedulesRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: GroupSchedule) -> GroupSchedule:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> GroupSchedule | None:
        return self._session.get(GroupSchedule, record_id)

    def delete(self, record_id: UUID) -> None:
        schedule = self.get(record_id)
        if schedule is None:
            return
        self._session.delete(schedule)
        self._session.commit()

    def list_all(self) -> list[GroupSchedule]:
        return list(self._session.scalars(select(GroupSchedule)))

    def list_by_group(self, group_id: UUID) -> list[GroupSchedule]:
        stmt = select(GroupSchedule).where(GroupSchedule.group_id == group_id)
        return list(self._session.scalars(stmt))

    def list_enabled(self) -> list[GroupSchedule]:
        stmt = select(GroupSchedule).where(GroupSchedule.enabled.is_(True))
        return list(self._session.scalars(stmt))

    def update_last_fired(self, schedule_id: UUID, fired_at: datetime) -> None:
        schedule = self.get(schedule_id)
        if schedule is None:
            return
        schedule.last_fired_at = fired_at
        self._session.commit()
