"""Item repositories."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from rss_digest.db.models import GroupItem, Item, ItemEvaluation, ItemSummary
from rss_digest.repository.base import ensure_id


class ItemsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: Item) -> Item:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> Item | None:
        return self._session.get(Item, record_id)

    def list_all(self) -> list[Item]:
        return list(self._session.scalars(select(Item)))

    def find_by_hash(self, canonical_url_hash: str) -> Item | None:
        stmt = select(Item).where(Item.canonical_url_hash == canonical_url_hash)
        return self._session.scalars(stmt).first()


class GroupItemsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: GroupItem) -> GroupItem:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def add_if_new(self, record: GroupItem) -> bool:
        existing = self._session.scalars(
            select(GroupItem).where(
                GroupItem.group_id == record.group_id,
                GroupItem.item_id == record.item_id,
            )
        ).first()
        if existing:
            return False
        self.add(record)
        return True

    def get(self, record_id: UUID) -> GroupItem | None:
        return self._session.get(GroupItem, record_id)

    def list_all(self) -> list[GroupItem]:
        return list(self._session.scalars(select(GroupItem)))

    def list_by_group(self, group_id: UUID) -> list[GroupItem]:
        stmt = select(GroupItem).where(GroupItem.group_id == group_id)
        return list(self._session.scalars(stmt))

    def list_since(self, group_id: UUID, since: datetime) -> list[GroupItem]:
        stmt = select(GroupItem).where(
            GroupItem.group_id == group_id, GroupItem.first_seen_at >= since
        )
        return list(self._session.scalars(stmt))


class ItemEvaluationsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: ItemEvaluation) -> ItemEvaluation:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> ItemEvaluation | None:
        return self._session.get(ItemEvaluation, record_id)

    def list_all(self) -> list[ItemEvaluation]:
        return list(self._session.scalars(select(ItemEvaluation)))

    def find(self, group_id: UUID, item_id: UUID) -> ItemEvaluation | None:
        stmt = select(ItemEvaluation).where(
            ItemEvaluation.group_id == group_id,
            ItemEvaluation.item_id == item_id,
        )
        return self._session.scalars(stmt).first()

    def list_by_group(self, group_id: UUID) -> list[ItemEvaluation]:
        stmt = select(ItemEvaluation).where(ItemEvaluation.group_id == group_id)
        return list(self._session.scalars(stmt))


class ItemSummariesRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: ItemSummary) -> ItemSummary:
        ensure_id(record)
        merged = self._session.merge(record)
        self._session.commit()
        return merged

    def get(self, record_id: UUID) -> ItemSummary | None:
        return self._session.get(ItemSummary, record_id)

    def list_all(self) -> list[ItemSummary]:
        return list(self._session.scalars(select(ItemSummary)))

    def find(self, group_id: UUID, item_id: UUID) -> ItemSummary | None:
        stmt = select(ItemSummary).where(
            ItemSummary.group_id == group_id,
            ItemSummary.item_id == item_id,
        )
        return self._session.scalars(stmt).first()

    def list_by_group(self, group_id: UUID) -> list[ItemSummary]:
        stmt = select(ItemSummary).where(ItemSummary.group_id == group_id)
        return list(self._session.scalars(stmt))
