"""Item repositories."""

from __future__ import annotations

from datetime import datetime
from typing import Dict
from uuid import UUID

from rss_digest.dedup import canonical_url_hash
from rss_digest.models import GroupItem, Item, ItemEvaluation, ItemSummary
from rss_digest.repository.base import InMemoryRepository


class ItemsRepo(InMemoryRepository):
    def __init__(self) -> None:
        super().__init__()
        self._index: Dict[str, UUID] = {}

    def add(self, record: Item) -> None:  # type: ignore[override]
        url_hash = record.canonical_url_hash or canonical_url_hash(record.canonical_url)
        if url_hash in self._index:
            return
        record.canonical_url_hash = url_hash
        super().add(record)
        self._index[url_hash] = record.id

    def find_by_hash(self, canonical_url_hash: str) -> Item | None:
        item_id = self._index.get(canonical_url_hash)
        if item_id is None:
            return None
        return self.get(item_id)  # type: ignore[return-value]


class GroupItemsRepo(InMemoryRepository):
    def __init__(self) -> None:
        super().__init__()
        self._index: Dict[tuple[UUID, UUID], UUID] = {}

    def add(self, record: GroupItem) -> None:  # type: ignore[override]
        key = (record.group_id, record.item_id)
        if key in self._index:
            return
        super().add(record)
        self._index[key] = record.id

    def add_if_new(self, record: GroupItem) -> bool:
        key = (record.group_id, record.item_id)
        if key in self._index:
            return False
        self.add(record)
        return True

    def list_by_group(self, group_id: UUID) -> list[GroupItem]:
        return [item for item in self.list_all() if item.group_id == group_id]

    def list_since(self, group_id: UUID, since: datetime) -> list[GroupItem]:
        return [
            item
            for item in self.list_by_group(group_id)
            if item.first_seen_at >= since
        ]


class ItemEvaluationsRepo(InMemoryRepository):
    def __init__(self) -> None:
        super().__init__()
        self._index: Dict[tuple[UUID, UUID], UUID] = {}

    def add(self, record: ItemEvaluation) -> None:  # type: ignore[override]
        key = (record.group_id, record.item_id)
        if key in self._index:
            return
        super().add(record)
        self._index[key] = record.id

    def find(self, group_id: UUID, item_id: UUID) -> ItemEvaluation | None:
        eval_id = self._index.get((group_id, item_id))
        if eval_id is None:
            return None
        return self.get(eval_id)  # type: ignore[return-value]

    def list_by_group(self, group_id: UUID) -> list[ItemEvaluation]:
        return [item for item in self.list_all() if item.group_id == group_id]


class ItemSummariesRepo(InMemoryRepository):
    def __init__(self) -> None:
        super().__init__()
        self._index: Dict[tuple[UUID, UUID], UUID] = {}

    def add(self, record: ItemSummary) -> None:  # type: ignore[override]
        key = (record.group_id, record.item_id)
        if key in self._index:
            return
        super().add(record)
        self._index[key] = record.id

    def find(self, group_id: UUID, item_id: UUID) -> ItemSummary | None:
        summary_id = self._index.get((group_id, item_id))
        if summary_id is None:
            return None
        return self.get(summary_id)  # type: ignore[return-value]

    def list_by_group(self, group_id: UUID) -> list[ItemSummary]:
        return [item for item in self.list_all() if item.group_id == group_id]
