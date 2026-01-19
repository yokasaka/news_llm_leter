"""HTTP RSS fetcher using httpx and feedparser."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from rss_digest.models import FeedSource
from rss_digest.services.rss.fetcher import FeedEntry, FeedFetchResult


class HttpFeedFetcher:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=10)

    def fetch(self, feed_source: FeedSource) -> FeedFetchResult:
        headers: dict[str, str] = {}
        if feed_source.etag:
            headers["If-None-Match"] = feed_source.etag
        if feed_source.last_modified:
            headers["If-Modified-Since"] = feed_source.last_modified
        response = self._client.get(feed_source.url, headers=headers)
        if response.status_code == 304:
            return FeedFetchResult(
                status_code=304,
                etag=feed_source.etag,
                last_modified=feed_source.last_modified,
            )
        if response.status_code >= 400:
            return FeedFetchResult(status_code=response.status_code)

        parsed = feedparser.parse(response.text)
        entries: list[FeedEntry] = []
        for entry in parsed.entries:
            guid = entry.get("id") or entry.get("guid") or entry.get("link") or ""
            url = entry.get("link") or ""
            published_at = _parse_datetime(entry.get("published"))
            if published_at is None and entry.get("updated"):
                published_at = _parse_datetime(entry.get("updated"))
            entries.append(FeedEntry(guid=guid, url=url, published_at=published_at))
        return FeedFetchResult(
            status_code=response.status_code,
            etag=response.headers.get("ETag"),
            last_modified=response.headers.get("Last-Modified"),
            entries=entries,
        )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
