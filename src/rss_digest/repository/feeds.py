"""Feed repositories."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from rss_digest.models import FeedItem, FeedSource, GroupFeed
from rss_digest.repository.base import InMemoryRepository, RepositoryError


class FeedSourcesRepo(InMemoryRepository):
    def add(self, record: FeedSource) -> None:  # type: ignore[override]
        super().add(record)

    def find_by_url(self, url: str) -> FeedSource | None:
        return next((feed for feed in self.list_all() if feed.url == url), None)

    def update_fetch_meta(
        self,
        feed_source_id: UUID,
        *,
        etag: Optional[str],
        last_modified: Optional[str],
        fetched_at: datetime,
        failures: int,
        status: str,
        fetch_count: int,
        not_modified_count: int,
        failure_count: int,
    ) -> None:
        feed = self.get(feed_source_id)
        if feed is None:
            raise RepositoryError("Feed source not found")
        self._records[feed_source_id] = replace(
            feed,
            etag=etag,
            last_modified=last_modified,
            last_fetch_at=fetched_at,
            consecutive_failures=failures,
            health_status=status,
            fetch_count=fetch_count,
            not_modified_count=not_modified_count,
            failure_count=failure_count,
        )


class GroupFeedsRepo(InMemoryRepository):
    def add(self, record: GroupFeed) -> None:  # type: ignore[override]
        super().add(record)

    def list_enabled(self, group_id: UUID) -> list[GroupFeed]:
        return [
            group_feed
            for group_feed in self.list_all()
            if group_feed.group_id == group_id and group_feed.enabled
        ]

    def list_by_group(self, group_id: UUID) -> list[GroupFeed]:
        return [group_feed for group_feed in self.list_all() if group_feed.group_id == group_id]


class FeedItemsRepo(InMemoryRepository):
    def __init__(self) -> None:
        super().__init__()
        self._index: Dict[tuple[UUID, str], UUID] = {}

    def add(self, record: FeedItem) -> None:  # type: ignore[override]
        key = (record.feed_source_id, record.guid_hash)
        if key in self._index:
            return
        super().add(record)
        self._index[key] = record.id

    def list_by_feed(self, feed_source_id: UUID) -> list[FeedItem]:
        return [
            item for item in self.list_all() if item.feed_source_id == feed_source_id
        ]

    def exists_guid(self, feed_source_id: UUID, guid_hash: str) -> bool:
        return (feed_source_id, guid_hash) in self._index
