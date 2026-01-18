"""Materialize feed items into canonical items and group associations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from rss_digest.dedup import canonical_url_hash, normalize_url
from rss_digest.models import FeedItem, GroupItem, Item
from rss_digest.repository import GroupItemsRepo, ItemsRepo


@dataclass
class MaterializedResult:
    items: list[Item]
    group_items: list[GroupItem]


class MaterializeService:
    def __init__(self, items: ItemsRepo, group_items: GroupItemsRepo) -> None:
        self._items = items
        self._group_items = group_items

    def materialize(
        self, group_id, feed_items: Iterable[FeedItem]
    ) -> MaterializedResult:
        new_items: list[Item] = []
        new_group_items: list[GroupItem] = []
        for feed_item in feed_items:
            canonical_url = normalize_url(feed_item.url)
            url_hash = canonical_url_hash(canonical_url)
            item = self._items.find_by_hash(url_hash)
            if item is None:
                item = Item(
                    canonical_url=canonical_url,
                    canonical_url_hash=url_hash,
                    first_seen_at=datetime.now(timezone.utc),
                )
                self._items.add(item)
                new_items.append(item)

            group_item = GroupItem(
                group_id=group_id,
                item_id=item.id,
                first_seen_at=datetime.now(timezone.utc),
            )
            if self._group_items.add_if_new(group_item):
                new_group_items.append(group_item)
        return MaterializedResult(items=new_items, group_items=new_group_items)
