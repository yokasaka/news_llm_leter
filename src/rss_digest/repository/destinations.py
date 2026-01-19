"""Destination repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from rss_digest.db.models import GroupDestination
from rss_digest.repository.base import ensure_id


class GroupDestinationsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: GroupDestination) -> GroupDestination:
        ensure_id(record)
        if record.type is None:
            record.type = "email"
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> GroupDestination | None:
        return self._session.get(GroupDestination, record_id)

    def delete(self, record_id: UUID) -> None:
        destination = self.get(record_id)
        if destination is None:
            return
        self._session.delete(destination)
        self._session.commit()

    def list_all(self) -> list[GroupDestination]:
        return list(self._session.scalars(select(GroupDestination)))

    def list_enabled(self, group_id: UUID) -> list[GroupDestination]:
        stmt = select(GroupDestination).where(
            GroupDestination.group_id == group_id,
            GroupDestination.enabled.is_(True),
        )
        return list(self._session.scalars(stmt))

    def list_by_group(self, group_id: UUID) -> list[GroupDestination]:
        stmt = select(GroupDestination).where(GroupDestination.group_id == group_id)
        return list(self._session.scalars(stmt))
