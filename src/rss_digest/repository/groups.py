"""Group repository."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from rss_digest.models import Group
from rss_digest.repository.base import InMemoryRepository, RepositoryError


class GroupsRepo(InMemoryRepository):
    def add(self, record: Group) -> None:  # type: ignore[override]
        super().add(record)

    def list_by_user(self, user_id: UUID) -> list[Group]:
        return [group for group in self.list_all() if group.user_id == user_id]

    def update_run_times(
        self, group_id: UUID, started_at: datetime, completed_at: datetime | None
    ) -> None:
        group = self.get(group_id)
        if group is None:
            raise RepositoryError("Group not found")
        updated = replace(
            group,
            last_run_started_at=started_at,
            last_run_completed_at=completed_at,
        )
        self._records[group_id] = updated
