from datetime import datetime, timezone

import httpx

from rss_digest.models import FeedSource
from rss_digest.repository import FeedItemsRepo, FeedSourcesRepo
from rss_digest.services.rss.fetcher import RssFetcher
from rss_digest.services.rss.http import HttpFeedFetcher


def test_http_fetcher_updates_etag_and_stores_items():
    rss_body = """<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>Example</title>
          <link>https://example.com/post</link>
          <guid>guid-1</guid>
          <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"ETag": "etag-1", "Last-Modified": "Wed, 01 Jan 2024 00:00:00 GMT"},
            text=rss_body,
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    fetcher = HttpFeedFetcher(client)
    feed_sources = FeedSourcesRepo()
    feed_items = FeedItemsRepo()
    source = FeedSource(url="https://example.com/rss")
    feed_sources.add(source)

    rss_fetcher = RssFetcher(feed_sources, feed_items, fetcher.fetch)
    items = rss_fetcher.fetch(source)

    assert len(items) == 1
    updated = feed_sources.get(source.id)
    assert updated.etag == "etag-1"
    assert updated.last_modified == "Wed, 01 Jan 2024 00:00:00 GMT"
    assert updated.fetch_count == 1
    assert updated.not_modified_count == 0


def test_http_fetcher_handles_304_not_modified():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["If-None-Match"] == "etag-1"
        assert request.headers["If-Modified-Since"] == "Wed, 01 Jan 2024 00:00:00 GMT"
        return httpx.Response(304)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    fetcher = HttpFeedFetcher(client)
    feed_sources = FeedSourcesRepo()
    feed_items = FeedItemsRepo()
    source = FeedSource(
        url="https://example.com/rss",
        etag="etag-1",
        last_modified="Wed, 01 Jan 2024 00:00:00 GMT",
        last_fetch_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        fetch_count=3,
        not_modified_count=1,
    )
    feed_sources.add(source)

    rss_fetcher = RssFetcher(feed_sources, feed_items, fetcher.fetch)
    items = rss_fetcher.fetch(source)

    assert items == []
    updated = feed_sources.get(source.id)
    assert updated.fetch_count == 4
    assert updated.not_modified_count == 2
