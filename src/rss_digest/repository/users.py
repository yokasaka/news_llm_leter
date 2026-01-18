"""User repository."""

from __future__ import annotations

from rss_digest.models import User
from rss_digest.repository.base import InMemoryRepository


class UsersRepo(InMemoryRepository):
    def add(self, record: User) -> None:  # type: ignore[override]
        super().add(record)

    def find_by_email(self, email: str) -> User | None:
        return next((user for user in self.list_all() if user.email == email), None)
