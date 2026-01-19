"""HTTP fetcher for RSS feeds with ETag/Last-Modified."""

from __future__ import annotations

from datetime import datetime, timezone
import feedparser
import httpx

from rss_digest.db.models import FeedSource
from rss_digest.services.rss.fetcher import FeedEntry, FeedFetchResult


def fetch_feed(feed_source: FeedSource) -> FeedFetchResult:
    headers: dict[str, str] = {}
    if feed_source.etag:
        headers["If-None-Match"] = feed_source.etag
    if feed_source.last_modified:
        headers["If-Modified-Since"] = feed_source.last_modified

    response = httpx.get(feed_source.url, headers=headers, timeout=15)
    if response.status_code == 304:
        return FeedFetchResult(status_code=304)

    response.raise_for_status()
    parsed = feedparser.parse(response.text)
    entries = [_to_entry(entry) for entry in parsed.entries]
    return FeedFetchResult(
        status_code=response.status_code,
        etag=response.headers.get("ETag"),
        last_modified=response.headers.get("Last-Modified"),
        entries=entries,
    )


def _to_entry(entry) -> FeedEntry:
    guid = entry.get("id") or entry.get("guid") or entry.get("link") or ""
    url = entry.get("link") or ""
    published_at = _parse_datetime(entry.get("published_parsed") or entry.get("updated_parsed"))
    return FeedEntry(guid=guid, url=url, published_at=published_at)


def _parse_datetime(value) -> datetime | None:
    if value is None:
        return None
    try:
        timestamp = datetime(*value[:6], tzinfo=timezone.utc)
    except Exception:
        return None
    return timestamp
