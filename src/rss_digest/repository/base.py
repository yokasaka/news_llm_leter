"""Base repository utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict
from uuid import UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RepositoryError(RuntimeError):
    """Base error for repository operations."""


class InMemoryRepository:
    def __init__(self) -> None:
        self._records: Dict[UUID, object] = {}

    def add(self, record: object) -> None:
        self._records[record.id] = record

    def get(self, record_id: UUID) -> object | None:
        return self._records.get(record_id)

    def list_all(self) -> list[object]:
        return list(self._records.values())

    def delete(self, record_id: UUID) -> None:
        self._records.pop(record_id, None)
