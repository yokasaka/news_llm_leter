"""Repository package for RSS digest workflow."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from rss_digest.db.session import build_session_factory
from rss_digest.repository.base import RepositoryError, utc_now
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
    session: Session

    @classmethod
    def build(cls, session: Session | None = None) -> "Repositories":
        if session is None:
            session = build_session_factory()()
        return cls(
            users=UsersRepo(session),
            groups=GroupsRepo(session),
            schedules=GroupSchedulesRepo(session),
            destinations=GroupDestinationsRepo(session),
            feed_sources=FeedSourcesRepo(session),
            group_feeds=GroupFeedsRepo(session),
            feed_items=FeedItemsRepo(session),
            items=ItemsRepo(session),
            group_items=GroupItemsRepo(session),
            evaluations=ItemEvaluationsRepo(session),
            summaries=ItemSummariesRepo(session),
            digests=DigestsRepo(session),
            deliveries=DeliveriesRepo(session),
            session=session,
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
