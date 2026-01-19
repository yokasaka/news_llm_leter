"""Domain models for the RSS digest pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


def new_id() -> UUID:
    return uuid4()


@dataclass
class User:
    id: UUID = field(default_factory=new_id)
    email: str = ""
    name: str = ""
    is_admin: bool = False
    timezone: str = "UTC"


@dataclass
class Group:
    id: UUID = field(default_factory=new_id)
    user_id: UUID | None = None
    name: str = ""
    description: str = ""
    is_enabled: bool = True
    last_run_started_at: datetime | None = None
    last_run_completed_at: datetime | None = None


@dataclass
class GroupSchedule:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    time_hhmm: str = ""
    enabled: bool = True
    last_fired_at: datetime | None = None


@dataclass
class GroupDestination:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    type: str = "email"
    destination: str = ""
    token_enc: str | None = None
    enabled: bool = True


@dataclass
class FeedSource:
    id: UUID = field(default_factory=new_id)
    url: str = ""
    etag: str | None = None
    last_modified: str | None = None
    last_fetch_at: datetime | None = None
    health_status: str = "healthy"
    consecutive_failures: int = 0
    fetch_count: int = 0
    not_modified_count: int = 0
    failure_count: int = 0


@dataclass
class GroupFeed:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    feed_source_id: UUID | None = None
    enabled: bool = True


@dataclass
class FeedItem:
    id: UUID = field(default_factory=new_id)
    feed_source_id: UUID | None = None
    guid_hash: str = ""
    url: str = ""
    published_at: datetime | None = None
    canonical_url_hash: str = ""


@dataclass
class Item:
    id: UUID = field(default_factory=new_id)
    canonical_url: str = ""
    canonical_url_hash: str = ""
    first_seen_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GroupItem:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    item_id: UUID | None = None
    first_seen_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ItemEvaluation:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    item_id: UUID | None = None
    relevance_score: float = 0.0
    decision: str = "exclude"
    reason: str = ""


@dataclass
class ItemSummary:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    item_id: UUID | None = None
    summary_md: str = ""


@dataclass
class Digest:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    scheduled_at: datetime | None = None
    markdown_body: str = ""
    storage_path: str = ""


@dataclass
class Delivery:
    id: UUID = field(default_factory=new_id)
    digest_id: UUID | None = None
    destination_id: UUID | None = None
    status: str = "pending"
    error_message: str | None = None


@dataclass
class JobRun:
    id: UUID = field(default_factory=new_id)
    group_id: UUID | None = None
    job_type: str = ""
    status: str = "pending"
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    error_message: str | None = None
