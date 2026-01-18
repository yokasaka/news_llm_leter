"""Service layer for RSS digest pipeline."""

from rss_digest.services.digest.builder import DigestBuilder
from rss_digest.services.digest.delivery import DeliveryService
from rss_digest.services.digest.storage import StorageService
from rss_digest.services.evaluation.relevance import KeywordRelevanceEvaluator, RelevanceEvaluator
from rss_digest.services.evaluation.service import EvaluationService
from rss_digest.services.evaluation.summarizer import SimpleSummarizer, Summarizer
from rss_digest.services.materialize.service import MaterializeService
from rss_digest.services.pipeline.service import GroupPipeline
from rss_digest.services.rss.discovery import RssDiscoveryService
from rss_digest.services.rss.fetcher import FeedEntry, FeedFetchResult, RssFetcher
from rss_digest.services.scheduler.service import SchedulerService

__all__ = [
    "DeliveryService",
    "DigestBuilder",
    "EvaluationService",
    "FeedEntry",
    "FeedFetchResult",
    "GroupPipeline",
    "KeywordRelevanceEvaluator",
    "MaterializeService",
    "RssDiscoveryService",
    "RssFetcher",
    "SchedulerService",
    "SimpleSummarizer",
    "StorageService",
    "Summarizer",
    "RelevanceEvaluator",
]
