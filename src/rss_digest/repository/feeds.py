"""Feed repositories."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from rss_digest.db.models import FeedItem, FeedSource, GroupFeed
from rss_digest.repository.base import RepositoryError, ensure_id


class FeedSourcesRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: FeedSource) -> FeedSource:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> FeedSource | None:
        return self._session.get(FeedSource, record_id)

    def list_all(self) -> list[FeedSource]:
        return list(self._session.scalars(select(FeedSource)))

    def find_by_url(self, url: str) -> FeedSource | None:
        return self._session.scalars(select(FeedSource).where(FeedSource.url == url)).first()

    def update_fetch_meta(
        self,
        feed_source_id: UUID,
        *,
        etag: Optional[str],
        last_modified: Optional[str],
        fetched_at: datetime,
        failures: int,
        status: str,
    ) -> None:
        feed = self.get(feed_source_id)
        if feed is None:
            raise RepositoryError("Feed source not found")
        feed.etag = etag
        feed.last_modified = last_modified
        feed.last_fetch_at = fetched_at
        feed.consecutive_failures = failures
        feed.health_status = status
        self._session.commit()


class GroupFeedsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: GroupFeed) -> GroupFeed:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> GroupFeed | None:
        return self._session.get(GroupFeed, record_id)

    def delete(self, record_id: UUID) -> None:
        group_feed = self.get(record_id)
        if group_feed is None:
            return
        self._session.delete(group_feed)
        self._session.commit()

    def list_all(self) -> list[GroupFeed]:
        return list(self._session.scalars(select(GroupFeed)))

    def list_enabled(self, group_id: UUID) -> list[GroupFeed]:
        stmt = select(GroupFeed).where(
            GroupFeed.group_id == group_id, GroupFeed.enabled.is_(True)
        )
        return list(self._session.scalars(stmt))

    def list_by_group(self, group_id: UUID) -> list[GroupFeed]:
        stmt = select(GroupFeed).where(GroupFeed.group_id == group_id)
        return list(self._session.scalars(stmt))


class FeedItemsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: FeedItem) -> FeedItem:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> FeedItem | None:
        return self._session.get(FeedItem, record_id)

    def list_all(self) -> list[FeedItem]:
        return list(self._session.scalars(select(FeedItem)))

    def list_by_feed(self, feed_source_id: UUID) -> list[FeedItem]:
        stmt = select(FeedItem).where(FeedItem.feed_source_id == feed_source_id)
        return list(self._session.scalars(stmt))

    def exists_guid(self, feed_source_id: UUID, guid_hash: str) -> bool:
        stmt = select(exists().where(
            FeedItem.feed_source_id == feed_source_id,
            FeedItem.guid_hash == guid_hash,
        ))
        return bool(self._session.execute(stmt).scalar())
