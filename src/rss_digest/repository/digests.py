"""Digest repositories."""

from __future__ import annotations

from uuid import UUID

from rss_digest.models import Delivery, Digest
from rss_digest.repository.base import InMemoryRepository


class DigestsRepo(InMemoryRepository):
    def add(self, record: Digest) -> None:  # type: ignore[override]
        super().add(record)

    def list_by_group(self, group_id: UUID) -> list[Digest]:
        return [digest for digest in self.list_all() if digest.group_id == group_id]


class DeliveriesRepo(InMemoryRepository):
    def add(self, record: Delivery) -> None:  # type: ignore[override]
        super().add(record)

    def list_by_digest(self, digest_id: UUID) -> list[Delivery]:
        return [delivery for delivery in self.list_all() if delivery.digest_id == digest_id]
