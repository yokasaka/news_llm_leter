"""Job run repositories."""

from __future__ import annotations

from uuid import UUID

from rss_digest.models import JobRun
from rss_digest.repository.base import InMemoryRepository


class JobRunsRepo(InMemoryRepository):
    def add(self, record: JobRun) -> None:  # type: ignore[override]
        super().add(record)

    def list_by_group(self, group_id: UUID) -> list[JobRun]:
        return [job for job in self.list_all() if job.group_id == group_id]
