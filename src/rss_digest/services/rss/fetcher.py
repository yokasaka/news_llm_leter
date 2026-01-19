"""RSS feed fetching service with ETag/Last-Modified support."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Callable, Iterable, Optional

from rss_digest.dedup import canonical_url_hash
from rss_digest.db.models import FeedItem, FeedSource
from rss_digest.repository import FeedItemsRepo, FeedSourcesRepo


@dataclass
class FeedEntry:
    guid: str
    url: str
    published_at: datetime | None = None


@dataclass
class FeedFetchResult:
    status_code: int
    etag: str | None = None
    last_modified: str | None = None
    entries: list[FeedEntry] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.entries is None:
            self.entries = []


FetchFunc = Callable[[FeedSource], FeedFetchResult]


class FetchError(RuntimeError):
    """Raised when fetching RSS feeds fails."""


class RssFetcher:
    def __init__(
        self,
        feed_sources: FeedSourcesRepo,
        feed_items: FeedItemsRepo,
        fetch_func: FetchFunc,
    ) -> None:
        self._feed_sources = feed_sources
        self._feed_items = feed_items
        self._fetch_func = fetch_func

    def fetch(self, feed_source: FeedSource) -> list[FeedItem]:
        try:
            result = self._fetch_func(feed_source)
        except Exception as exc:  # noqa: BLE001 - surface failure
            self._mark_failure(feed_source)
            raise FetchError(str(exc)) from exc

        if result.status_code == 304:
            self._mark_success(feed_source, result)
            return []
        if result.status_code >= 400:
            self._mark_failure(feed_source)
            raise FetchError(f"status={result.status_code}")

        new_items: list[FeedItem] = []
        for entry in result.entries:
            guid_hash = self._hash_guid(entry.guid)
            if self._feed_items.exists_guid(feed_source.id, guid_hash):
                continue
            feed_item = FeedItem(
                feed_source_id=feed_source.id,
                guid_hash=guid_hash,
                url=entry.url,
                published_at=entry.published_at,
                canonical_url_hash=canonical_url_hash(entry.url),
            )
            feed_item = self._feed_items.add(feed_item)
            new_items.append(feed_item)

        self._mark_success(feed_source, result)
        return new_items

    def fetch_group(self, feed_sources: Iterable[FeedSource]) -> list[FeedItem]:
        new_items: list[FeedItem] = []
        for feed_source in feed_sources:
            new_items.extend(self.fetch(feed_source))
        return new_items

    def _mark_success(self, feed_source: FeedSource, result: FeedFetchResult) -> None:
        self._feed_sources.update_fetch_meta(
            feed_source.id,
            etag=result.etag,
            last_modified=result.last_modified,
            fetched_at=datetime.now(timezone.utc),
            failures=0,
            status="healthy",
        )

    def _mark_failure(self, feed_source: FeedSource) -> None:
        failures = feed_source.consecutive_failures + 1
        status = "dead" if failures >= 5 else "degraded"
        self._feed_sources.update_fetch_meta(
            feed_source.id,
            etag=feed_source.etag,
            last_modified=feed_source.last_modified,
            fetched_at=datetime.now(timezone.utc),
            failures=failures,
            status=status,
        )

    @staticmethod
    def _hash_guid(guid: str) -> str:
        return hashlib.sha256(guid.encode("utf-8")).hexdigest()
