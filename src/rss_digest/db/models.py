"""SQLAlchemy ORM models for the RSS digest pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rss_digest.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")

    groups: Mapped[list["Group"]] = relationship(back_populates="user")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_run_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="groups")
    schedules: Mapped[list["GroupSchedule"]] = relationship(back_populates="group")
    destinations: Mapped[list["GroupDestination"]] = relationship(back_populates="group")
    feeds: Mapped[list["GroupFeed"]] = relationship(back_populates="group")
    items: Mapped[list["GroupItem"]] = relationship(back_populates="group")


class GroupSchedule(Base):
    __tablename__ = "group_schedules"
    __table_args__ = (
        UniqueConstraint("group_id", "time_hhmm", name="uq_group_schedules_time"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    time_hhmm: Mapped[str] = mapped_column(String(5), nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    group: Mapped["Group"] = relationship(back_populates="schedules")


class GroupDestination(Base):
    __tablename__ = "group_destinations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    token_enc: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

    group: Mapped["Group"] = relationship(back_populates="destinations")


class FeedSource(Base):
    __tablename__ = "feed_sources"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[str | None] = mapped_column(Text)
    last_fetch_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    health_status: Mapped[str] = mapped_column(String(32), nullable=False, default="healthy")
    consecutive_failures: Mapped[int] = mapped_column(default=0, nullable=False)

    group_feeds: Mapped[list["GroupFeed"]] = relationship(back_populates="feed_source")
    feed_items: Mapped[list["FeedItem"]] = relationship(back_populates="feed_source")


class GroupFeed(Base):
    __tablename__ = "group_feeds"
    __table_args__ = (
        UniqueConstraint("group_id", "feed_source_id", name="uq_group_feeds_source"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    feed_source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("feed_sources.id"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

    group: Mapped["Group"] = relationship(back_populates="feeds")
    feed_source: Mapped["FeedSource"] = relationship(back_populates="group_feeds")


class FeedItem(Base):
    __tablename__ = "feed_items"
    __table_args__ = (
        UniqueConstraint("feed_source_id", "guid_hash", name="uq_feed_items_guid"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    feed_source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("feed_sources.id"), nullable=False
    )
    guid_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canonical_url_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    feed_source: Mapped["FeedSource"] = relationship(back_populates="feed_items")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("canonical_url_hash", name="uq_items_canonical"),)

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    group_items: Mapped[list["GroupItem"]] = relationship(back_populates="item")
    evaluations: Mapped[list["ItemEvaluation"]] = relationship(back_populates="item")
    summaries: Mapped[list["ItemSummary"]] = relationship(back_populates="item")


class GroupItem(Base):
    __tablename__ = "group_items"
    __table_args__ = (
        UniqueConstraint("group_id", "item_id", name="uq_group_items_item"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    group: Mapped["Group"] = relationship(back_populates="items")
    item: Mapped["Item"] = relationship(back_populates="group_items")


class ItemEvaluation(Base):
    __tablename__ = "item_evaluations"
    __table_args__ = (
        UniqueConstraint("group_id", "item_id", name="uq_item_evaluations_item"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    relevance_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    decision: Mapped[str] = mapped_column(String(32), nullable=False, default="exclude")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")

    item: Mapped["Item"] = relationship(back_populates="evaluations")


class ItemSummary(Base):
    __tablename__ = "item_summaries"
    __table_args__ = (
        UniqueConstraint("group_id", "item_id", name="uq_item_summaries_item"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    summary_md: Mapped[str] = mapped_column(Text, nullable=False, default="")

    item: Mapped["Item"] = relationship(back_populates="summaries")


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    markdown_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    storage_path: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )
    digest_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("digests.id"), nullable=False
    )
    destination_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("group_destinations.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
