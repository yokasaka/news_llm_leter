"""Factories for building pipeline services."""

from __future__ import annotations

import os
from pathlib import Path

from rss_digest.repository import Repositories
from rss_digest.services.digest.builder import DigestBuilder
from rss_digest.services.digest.delivery import DeliveryService, EmailSender, SlackSender
from rss_digest.services.digest.storage import StorageService
from rss_digest.services.evaluation.relevance import KeywordRelevanceEvaluator
from rss_digest.services.evaluation.service import EvaluationService
from rss_digest.services.evaluation.summarizer import SimpleSummarizer
from rss_digest.services.materialize.service import MaterializeService
from rss_digest.services.pipeline.service import GroupPipeline
from rss_digest.services.rss.fetcher import RssFetcher
from rss_digest.services.rss.http import HttpFeedFetcher


def build_repositories(db_path: str | None = None) -> Repositories:
    if db_path:
        return Repositories.build_sqlite(Path(db_path))
    env_path = os.getenv("RSS_DIGEST_DB_PATH")
    if env_path:
        return Repositories.build_sqlite(Path(env_path))
    return Repositories.build()


def build_pipeline(repositories: Repositories) -> GroupPipeline:
    http_fetcher = HttpFeedFetcher()
    rss_fetcher = RssFetcher(repositories.feed_sources, repositories.feed_items, http_fetcher.fetch)
    materializer = MaterializeService(repositories.items, repositories.group_items)
    evaluator = EvaluationService(
        repositories.items,
        repositories.group_items,
        repositories.evaluations,
        repositories.summaries,
        KeywordRelevanceEvaluator(),
        SimpleSummarizer(),
    )
    digest_builder = DigestBuilder()
    storage_path = Path(os.getenv("RSS_DIGEST_STORAGE_PATH", "/tmp/rss_digest"))
    storage = StorageService(storage_path)
    email_sender = EmailSender(
        host=os.getenv("RSS_DIGEST_SMTP_HOST", "localhost"),
        port=int(os.getenv("RSS_DIGEST_SMTP_PORT", "1025")),
        username=os.getenv("RSS_DIGEST_SMTP_USERNAME"),
        password=os.getenv("RSS_DIGEST_SMTP_PASSWORD"),
        from_address=os.getenv("RSS_DIGEST_SMTP_FROM", "rss-digest@example.com"),
    )
    slack_sender = SlackSender()
    delivery = DeliveryService(repositories.deliveries, email_sender, slack_sender)
    return GroupPipeline(
        repositories,
        rss_fetcher,
        materializer,
        evaluator,
        digest_builder,
        storage,
        delivery,
    )
