"""Group pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID

from rss_digest.db.models import Digest, FeedSource, Group
from rss_digest.repository import (
    DigestsRepo,
    FeedSourcesRepo,
    GroupDestinationsRepo,
    GroupFeedsRepo,
    GroupsRepo,
    Repositories,
)
from rss_digest.services.digest.delivery import DeliveryService
from rss_digest.services.digest.builder import DigestBuilder
from rss_digest.services.evaluation.service import EvaluationService
from rss_digest.services.materialize.service import MaterializeService
from rss_digest.services.rss.fetcher import RssFetcher
from rss_digest.services.digest.storage import StorageService


LOOKBACK_HOURS_DEFAULT = 24


@dataclass
class PipelineResult:
    digest: Digest


class GroupPipeline:
    def __init__(
        self,
        repositories: Repositories,
        fetcher: RssFetcher,
        materializer: MaterializeService,
        evaluator: EvaluationService,
        digest_builder: DigestBuilder,
        storage: StorageService,
        delivery: DeliveryService,
        lookback_hours: int = LOOKBACK_HOURS_DEFAULT,
    ) -> None:
        self._repositories = repositories
        self._groups = repositories.groups
        self._group_feeds = repositories.group_feeds
        self._feed_sources = repositories.feed_sources
        self._destinations = repositories.destinations
        self._digests = repositories.digests
        self._fetcher = fetcher
        self._materializer = materializer
        self._evaluator = evaluator
        self._digest_builder = digest_builder
        self._storage = storage
        self._delivery = delivery
        self._lookback_hours = lookback_hours

    def run(self, group_id: UUID, scheduled_at: datetime) -> PipelineResult:
        group = self._groups.get(group_id)
        if group is None or not group.is_enabled:
            raise ValueError("Group not found or disabled")
        started_at = datetime.now(timezone.utc)
        since = self._determine_since(group, scheduled_at)
        feed_sources = self._load_feed_sources(group_id)
        feed_items = self._fetcher.fetch_group(feed_sources)
        materialized = self._materializer.materialize(group_id, feed_items)
        evaluation_result = self._evaluator.evaluate_since(group_id, since)
        digest = self._compose_digest(
            group,
            scheduled_at,
            evaluation_result,
        )
        digest = self._digests.add(digest)
        storage_result = self._storage.save_digest(
            group_id=group_id,
            scheduled_at=scheduled_at,
            markdown=digest.markdown_body,
        )
        digest.storage_path = storage_result.path
        digest = self._digests.add(digest)
        destinations = self._destinations.list_enabled(group_id)
        self._delivery.deliver(digest.id, destinations)
        self._groups.update_run_times(group_id, started_at, datetime.now(timezone.utc))
        return PipelineResult(digest=digest)

    def _determine_since(self, group: Group, scheduled_at: datetime) -> datetime:
        if group.last_run_started_at:
            return group.last_run_started_at
        return scheduled_at - timedelta(hours=self._lookback_hours)

    def _load_feed_sources(self, group_id: UUID) -> list[FeedSource]:
        group_feeds = self._group_feeds.list_enabled(group_id)
        sources: list[FeedSource] = []
        for group_feed in group_feeds:
            source = self._feed_sources.get(group_feed.feed_source_id)
            if source is not None:
                sources.append(source)
        return sources

    def _compose_digest(
        self,
        group: Group,
        scheduled_at: datetime,
        evaluation_result,
    ) -> Digest:
        evaluations = [
            evaluation
            for evaluation in evaluation_result.evaluations
            if evaluation.decision == "include"
        ]
        items = [
            self._repositories.items.get(evaluation.item_id)
            for evaluation in evaluations
        ]
        valid_items = [item for item in items if item is not None]
        summaries = evaluation_result.summaries
        sections = self._digest_builder.from_items(valid_items, summaries)
        markdown = self._digest_builder.compose(group, scheduled_at, sections)
        return Digest(
            group_id=group.id,
            scheduled_at=scheduled_at,
            markdown_body=markdown,
        )
