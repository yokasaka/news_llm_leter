"""Repository package for RSS digest workflow."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from uuid import UUID

from rss_digest.repository.base import InMemoryRepository, RepositoryError, utc_now
from rss_digest.repository.destinations import GroupDestinationsRepo
from rss_digest.repository.digests import DeliveriesRepo, DigestsRepo
from rss_digest.repository.feeds import FeedItemsRepo, FeedSourcesRepo, GroupFeedsRepo
from rss_digest.repository.groups import GroupsRepo
from rss_digest.repository.items import (
    GroupItemsRepo,
    ItemEvaluationsRepo,
    ItemSummariesRepo,
    ItemsRepo,
)
from rss_digest.repository.schedules import GroupSchedulesRepo
from rss_digest.repository.users import UsersRepo


@dataclass
class Repositories:
    users: UsersRepo
    groups: GroupsRepo
    schedules: GroupSchedulesRepo
    destinations: GroupDestinationsRepo
    feed_sources: FeedSourcesRepo
    group_feeds: GroupFeedsRepo
    feed_items: FeedItemsRepo
    items: ItemsRepo
    group_items: GroupItemsRepo
    evaluations: ItemEvaluationsRepo
    summaries: ItemSummariesRepo
    digests: DigestsRepo
    deliveries: DeliveriesRepo

    @classmethod
    def build(cls) -> "Repositories":
        return cls(
            users=UsersRepo(),
            groups=GroupsRepo(),
            schedules=GroupSchedulesRepo(),
            destinations=GroupDestinationsRepo(),
            feed_sources=FeedSourcesRepo(),
            group_feeds=GroupFeedsRepo(),
            feed_items=FeedItemsRepo(),
            items=ItemsRepo(),
            group_items=GroupItemsRepo(),
            evaluations=ItemEvaluationsRepo(),
            summaries=ItemSummariesRepo(),
            digests=DigestsRepo(),
            deliveries=DeliveriesRepo(),
        )


def ensure_unique(values: Iterable[UUID]) -> Sequence[UUID]:
    seen: set[UUID] = set()
    unique_values: list[UUID] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


__all__ = [
    "DeliveriesRepo",
    "DigestsRepo",
    "FeedItemsRepo",
    "FeedSourcesRepo",
    "GroupDestinationsRepo",
    "GroupFeedsRepo",
    "GroupItemsRepo",
    "GroupSchedulesRepo",
    "InMemoryRepository",
    "ItemEvaluationsRepo",
    "ItemSummariesRepo",
    "ItemsRepo",
    "Repositories",
    "RepositoryError",
    "UsersRepo",
    "GroupsRepo",
    "ensure_unique",
    "utc_now",
]
