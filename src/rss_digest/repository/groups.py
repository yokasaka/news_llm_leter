"""Group repository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from rss_digest.db.models import Group
from rss_digest.repository.base import RepositoryError, ensure_id


class GroupsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: Group) -> Group:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> Group | None:
        return self._session.get(Group, record_id)

    def list_all(self) -> list[Group]:
        return list(self._session.scalars(select(Group)))

    def list_by_user(self, user_id: UUID) -> list[Group]:
        return list(self._session.scalars(select(Group).where(Group.user_id == user_id)))

    def delete(self, record_id: UUID) -> None:
        group = self.get(record_id)
        if group is None:
            return
        self._session.delete(group)
        self._session.commit()

    def update_run_times(
        self, group_id: UUID, started_at: datetime, completed_at: datetime | None
    ) -> None:
        group = self.get(group_id)
        if group is None:
            raise RepositoryError("Group not found")
        group.last_run_started_at = started_at
        group.last_run_completed_at = completed_at
        self._session.commit()
