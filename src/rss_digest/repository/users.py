"""User repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from rss_digest.db.models import User
from rss_digest.repository.base import ensure_id


class UsersRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: User) -> User:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> User | None:
        return self._session.get(User, record_id)

    def list_all(self) -> list[User]:
        return list(self._session.scalars(select(User)))

    def find_by_email(self, email: str) -> User | None:
        return self._session.scalars(select(User).where(User.email == email)).first()
