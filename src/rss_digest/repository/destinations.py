"""Destination repository."""

from __future__ import annotations

from uuid import UUID

from rss_digest.models import GroupDestination
from rss_digest.repository.base import InMemoryRepository


class GroupDestinationsRepo(InMemoryRepository):
    def add(self, record: GroupDestination) -> None:  # type: ignore[override]
        super().add(record)

    def list_enabled(self, group_id: UUID) -> list[GroupDestination]:
        return [
            destination
            for destination in self.list_all()
            if destination.group_id == group_id and destination.enabled
        ]

    def list_by_group(self, group_id: UUID) -> list[GroupDestination]:
        return [
            destination
            for destination in self.list_all()
            if destination.group_id == group_id
        ]
