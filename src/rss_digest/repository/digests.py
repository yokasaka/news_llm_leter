"""Digest repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from rss_digest.db.models import Delivery, Digest
from rss_digest.repository.base import ensure_id


class DigestsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: Digest) -> Digest:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> Digest | None:
        return self._session.get(Digest, record_id)

    def list_all(self) -> list[Digest]:
        return list(self._session.scalars(select(Digest)))

    def list_by_group(self, group_id: UUID) -> list[Digest]:
        stmt = select(Digest).where(Digest.group_id == group_id)
        return list(self._session.scalars(stmt))


class DeliveriesRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: Delivery) -> Delivery:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> Delivery | None:
        return self._session.get(Delivery, record_id)

    def list_all(self) -> list[Delivery]:
        return list(self._session.scalars(select(Delivery)))

    def list_by_digest(self, digest_id: UUID) -> list[Delivery]:
        stmt = select(Delivery).where(Delivery.digest_id == digest_id)
        return list(self._session.scalars(stmt))
