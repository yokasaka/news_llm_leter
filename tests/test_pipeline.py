from datetime import datetime, timezone
from pathlib import Path

from rss_digest.db.models import FeedSource, Group, GroupDestination, GroupFeed, User
from rss_digest.services.digest.delivery import DeliveryService
from rss_digest.services.digest.builder import DigestBuilder
from rss_digest.services.evaluation.service import EvaluationService
from rss_digest.services.materialize.service import MaterializeService
from rss_digest.services.pipeline.service import GroupPipeline
from rss_digest.services.evaluation.relevance import KeywordRelevanceEvaluator
from rss_digest.services.rss.fetcher import FeedEntry, FeedFetchResult, RssFetcher
from rss_digest.services.digest.storage import StorageService
from rss_digest.services.evaluation.summarizer import SimpleSummarizer


def test_group_pipeline_runs_and_persists_digest(tmp_path, repositories):
    repos = repositories
    user = repos.users.add(User(email="user@example.com", timezone="UTC"))
    group = repos.groups.add(Group(user_id=user.id, name="Tech"))
    feed_source = repos.feed_sources.add(FeedSource(url="https://example.com/rss"))
    group_feed = GroupFeed(group_id=group.id, feed_source_id=feed_source.id)
    destination = GroupDestination(group_id=group.id, destination="user@example.com")
    repos.group_feeds.add(group_feed)
    repos.destinations.add(destination)

    def fetch_func(source: FeedSource) -> FeedFetchResult:
        return FeedFetchResult(
            status_code=200,
            entries=[
                FeedEntry(
                    guid="guid-1",
                    url="https://example.com/news/important",
                    published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                )
            ],
        )

    fetcher = RssFetcher(repos.feed_sources, repos.feed_items, fetch_func)
    materializer = MaterializeService(repos.items, repos.group_items)
    evaluator = EvaluationService(
        repos.items,
        repos.group_items,
        repos.evaluations,
        repos.summaries,
        KeywordRelevanceEvaluator(include_keywords=["important"]),
        SimpleSummarizer(),
    )
    builder = DigestBuilder()
    storage = StorageService(tmp_path)
    delivery = DeliveryService(repos.deliveries)

    pipeline = GroupPipeline(
        repos,
        fetcher,
        materializer,
        evaluator,
        builder,
        storage,
        delivery,
    )

    scheduled_at = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    result = pipeline.run(group.id, scheduled_at)

    path = Path(result.digest.storage_path)
    assert path.exists()
    assert str(path).startswith(str(tmp_path))
