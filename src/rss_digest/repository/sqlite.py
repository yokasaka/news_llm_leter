"""SQLite-backed repositories."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from rss_digest.dedup import canonical_url_hash
from rss_digest.models import (
    Delivery,
    Digest,
    FeedItem,
    FeedSource,
    Group,
    GroupDestination,
    GroupFeed,
    GroupItem,
    GroupSchedule,
    Item,
    ItemEvaluation,
    ItemSummary,
    JobRun,
    User,
)


def _to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _from_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


class SqliteDatabase:
    def __init__(self, path: Path) -> None:
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def _create_tables(self) -> None:
        cursor = self._connection.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                name TEXT,
                is_admin INTEGER,
                timezone TEXT
            );
            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT,
                description TEXT,
                is_enabled INTEGER,
                last_run_started_at TEXT,
                last_run_completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS group_schedules (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                time_hhmm TEXT,
                enabled INTEGER,
                last_fired_at TEXT,
                UNIQUE(group_id, time_hhmm)
            );
            CREATE TABLE IF NOT EXISTS group_destinations (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                type TEXT,
                destination TEXT,
                token_enc TEXT,
                enabled INTEGER
            );
            CREATE TABLE IF NOT EXISTS feed_sources (
                id TEXT PRIMARY KEY,
                url TEXT UNIQUE,
                etag TEXT,
                last_modified TEXT,
                last_fetch_at TEXT,
                health_status TEXT,
                consecutive_failures INTEGER,
                fetch_count INTEGER,
                not_modified_count INTEGER,
                failure_count INTEGER
            );
            CREATE TABLE IF NOT EXISTS group_feeds (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                feed_source_id TEXT,
                enabled INTEGER
            );
            CREATE TABLE IF NOT EXISTS feed_items (
                id TEXT PRIMARY KEY,
                feed_source_id TEXT,
                guid_hash TEXT,
                url TEXT,
                published_at TEXT,
                canonical_url_hash TEXT,
                UNIQUE(feed_source_id, guid_hash)
            );
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                canonical_url TEXT,
                canonical_url_hash TEXT UNIQUE,
                first_seen_at TEXT
            );
            CREATE TABLE IF NOT EXISTS group_items (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                item_id TEXT,
                first_seen_at TEXT,
                UNIQUE(group_id, item_id)
            );
            CREATE TABLE IF NOT EXISTS item_evaluations (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                item_id TEXT,
                relevance_score REAL,
                decision TEXT,
                reason TEXT,
                UNIQUE(group_id, item_id)
            );
            CREATE TABLE IF NOT EXISTS item_summaries (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                item_id TEXT,
                summary_md TEXT,
                UNIQUE(group_id, item_id)
            );
            CREATE TABLE IF NOT EXISTS digests (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                scheduled_at TEXT,
                markdown_body TEXT,
                storage_path TEXT
            );
            CREATE TABLE IF NOT EXISTS deliveries (
                id TEXT PRIMARY KEY,
                digest_id TEXT,
                destination_id TEXT,
                status TEXT,
                error_message TEXT
            );
            CREATE TABLE IF NOT EXISTS job_runs (
                id TEXT PRIMARY KEY,
                group_id TEXT,
                job_type TEXT,
                status TEXT,
                started_at TEXT,
                finished_at TEXT,
                error_message TEXT
            );
            """
        )
        self._connection.commit()


class SqliteRepo:
    def __init__(self, db: SqliteDatabase) -> None:
        self._db = db

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        self._db.connection.execute(sql, params)
        self._db.connection.commit()

    def _fetchone(self, sql: str, params: tuple[Any, ...]) -> sqlite3.Row | None:
        cursor = self._db.connection.execute(sql, params)
        return cursor.fetchone()

    def _fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        cursor = self._db.connection.execute(sql, params)
        return list(cursor.fetchall())


class SqliteUsersRepo(SqliteRepo):
    def add(self, record: User) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO users (id, email, name, is_admin, timezone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(record.id), record.email, record.name, int(record.is_admin), record.timezone),
        )

    def get(self, record_id: UUID) -> User | None:
        row = self._fetchone("SELECT * FROM users WHERE id = ?", (str(record_id),))
        return _row_to_user(row)

    def list_all(self) -> list[User]:
        return [_row_to_user(row) for row in self._fetchall("SELECT * FROM users")]

    def delete(self, record_id: UUID) -> None:
        self._execute("DELETE FROM users WHERE id = ?", (str(record_id),))

    def find_by_email(self, email: str) -> User | None:
        row = self._fetchone("SELECT * FROM users WHERE email = ?", (email,))
        return _row_to_user(row)


class SqliteGroupsRepo(SqliteRepo):
    def add(self, record: Group) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO groups (
                id, user_id, name, description, is_enabled,
                last_run_started_at, last_run_completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.user_id) if record.user_id else None,
                record.name,
                record.description,
                int(record.is_enabled),
                _to_iso(record.last_run_started_at),
                _to_iso(record.last_run_completed_at),
            ),
        )

    def get(self, record_id: UUID) -> Group | None:
        row = self._fetchone("SELECT * FROM groups WHERE id = ?", (str(record_id),))
        return _row_to_group(row)

    def list_all(self) -> list[Group]:
        return [_row_to_group(row) for row in self._fetchall("SELECT * FROM groups")]

    def delete(self, record_id: UUID) -> None:
        self._execute("DELETE FROM groups WHERE id = ?", (str(record_id),))

    def list_by_user(self, user_id: UUID) -> list[Group]:
        return [
            _row_to_group(row)
            for row in self._fetchall("SELECT * FROM groups WHERE user_id = ?", (str(user_id),))
        ]

    def update_run_times(
        self, group_id: UUID, started_at: datetime, completed_at: datetime | None
    ) -> None:
        self._execute(
            """
            UPDATE groups
            SET last_run_started_at = ?, last_run_completed_at = ?
            WHERE id = ?
            """,
            (_to_iso(started_at), _to_iso(completed_at), str(group_id)),
        )


class SqliteGroupSchedulesRepo(SqliteRepo):
    def add(self, record: GroupSchedule) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO group_schedules (
                id, group_id, time_hhmm, enabled, last_fired_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                record.time_hhmm,
                int(record.enabled),
                _to_iso(record.last_fired_at),
            ),
        )

    def get(self, record_id: UUID) -> GroupSchedule | None:
        row = self._fetchone("SELECT * FROM group_schedules WHERE id = ?", (str(record_id),))
        return _row_to_schedule(row)

    def list_all(self) -> list[GroupSchedule]:
        return [_row_to_schedule(row) for row in self._fetchall("SELECT * FROM group_schedules")]

    def delete(self, record_id: UUID) -> None:
        self._execute("DELETE FROM group_schedules WHERE id = ?", (str(record_id),))

    def list_enabled(self) -> list[GroupSchedule]:
        return [
            _row_to_schedule(row)
            for row in self._fetchall(
                "SELECT * FROM group_schedules WHERE enabled = 1"
            )
        ]

    def list_by_group(self, group_id: UUID) -> list[GroupSchedule]:
        return [
            _row_to_schedule(row)
            for row in self._fetchall(
                "SELECT * FROM group_schedules WHERE group_id = ?",
                (str(group_id),),
            )
        ]

    def update_last_fired(self, schedule_id: UUID, fired_at: datetime) -> None:
        self._execute(
            "UPDATE group_schedules SET last_fired_at = ? WHERE id = ?",
            (_to_iso(fired_at), str(schedule_id)),
        )


class SqliteGroupDestinationsRepo(SqliteRepo):
    def add(self, record: GroupDestination) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO group_destinations (
                id, group_id, type, destination, token_enc, enabled
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                record.type,
                record.destination,
                record.token_enc,
                int(record.enabled),
            ),
        )

    def get(self, record_id: UUID) -> GroupDestination | None:
        row = self._fetchone("SELECT * FROM group_destinations WHERE id = ?", (str(record_id),))
        return _row_to_destination(row)

    def list_all(self) -> list[GroupDestination]:
        return [
            _row_to_destination(row) for row in self._fetchall("SELECT * FROM group_destinations")
        ]

    def delete(self, record_id: UUID) -> None:
        self._execute("DELETE FROM group_destinations WHERE id = ?", (str(record_id),))

    def list_enabled(self, group_id: UUID) -> list[GroupDestination]:
        return [
            _row_to_destination(row)
            for row in self._fetchall(
                "SELECT * FROM group_destinations WHERE group_id = ? AND enabled = 1",
                (str(group_id),),
            )
        ]

    def list_by_group(self, group_id: UUID) -> list[GroupDestination]:
        return [
            _row_to_destination(row)
            for row in self._fetchall(
                "SELECT * FROM group_destinations WHERE group_id = ?", (str(group_id),)
            )
        ]


class SqliteFeedSourcesRepo(SqliteRepo):
    def add(self, record: FeedSource) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO feed_sources (
                id, url, etag, last_modified, last_fetch_at, health_status,
                consecutive_failures, fetch_count, not_modified_count, failure_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                record.url,
                record.etag,
                record.last_modified,
                _to_iso(record.last_fetch_at),
                record.health_status,
                record.consecutive_failures,
                record.fetch_count,
                record.not_modified_count,
                record.failure_count,
            ),
        )

    def get(self, record_id: UUID) -> FeedSource | None:
        row = self._fetchone("SELECT * FROM feed_sources WHERE id = ?", (str(record_id),))
        return _row_to_feed_source(row)

    def list_all(self) -> list[FeedSource]:
        return [_row_to_feed_source(row) for row in self._fetchall("SELECT * FROM feed_sources")]

    def delete(self, record_id: UUID) -> None:
        self._execute("DELETE FROM feed_sources WHERE id = ?", (str(record_id),))

    def find_by_url(self, url: str) -> FeedSource | None:
        row = self._fetchone("SELECT * FROM feed_sources WHERE url = ?", (url,))
        return _row_to_feed_source(row)

    def update_fetch_meta(
        self,
        feed_source_id: UUID,
        *,
        etag: str | None,
        last_modified: str | None,
        fetched_at: datetime,
        failures: int,
        status: str,
        fetch_count: int,
        not_modified_count: int,
        failure_count: int,
    ) -> None:
        self._execute(
            """
            UPDATE feed_sources
            SET etag = ?, last_modified = ?, last_fetch_at = ?, health_status = ?,
                consecutive_failures = ?, fetch_count = ?, not_modified_count = ?,
                failure_count = ?
            WHERE id = ?
            """,
            (
                etag,
                last_modified,
                _to_iso(fetched_at),
                status,
                failures,
                fetch_count,
                not_modified_count,
                failure_count,
                str(feed_source_id),
            ),
        )


class SqliteGroupFeedsRepo(SqliteRepo):
    def add(self, record: GroupFeed) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO group_feeds (id, group_id, feed_source_id, enabled)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                str(record.feed_source_id) if record.feed_source_id else None,
                int(record.enabled),
            ),
        )

    def get(self, record_id: UUID) -> GroupFeed | None:
        row = self._fetchone("SELECT * FROM group_feeds WHERE id = ?", (str(record_id),))
        return _row_to_group_feed(row)

    def list_all(self) -> list[GroupFeed]:
        return [_row_to_group_feed(row) for row in self._fetchall("SELECT * FROM group_feeds")]

    def delete(self, record_id: UUID) -> None:
        self._execute("DELETE FROM group_feeds WHERE id = ?", (str(record_id),))

    def list_enabled(self, group_id: UUID) -> list[GroupFeed]:
        return [
            _row_to_group_feed(row)
            for row in self._fetchall(
                "SELECT * FROM group_feeds WHERE group_id = ? AND enabled = 1",
                (str(group_id),),
            )
        ]

    def list_by_group(self, group_id: UUID) -> list[GroupFeed]:
        return [
            _row_to_group_feed(row)
            for row in self._fetchall(
                "SELECT * FROM group_feeds WHERE group_id = ?", (str(group_id),)
            )
        ]


class SqliteFeedItemsRepo(SqliteRepo):
    def add(self, record: FeedItem) -> None:
        self._execute(
            """
            INSERT OR IGNORE INTO feed_items (
                id, feed_source_id, guid_hash, url, published_at, canonical_url_hash
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.feed_source_id) if record.feed_source_id else None,
                record.guid_hash,
                record.url,
                _to_iso(record.published_at),
                record.canonical_url_hash,
            ),
        )

    def list_by_feed(self, feed_source_id: UUID) -> list[FeedItem]:
        return [
            _row_to_feed_item(row)
            for row in self._fetchall(
                "SELECT * FROM feed_items WHERE feed_source_id = ?", (str(feed_source_id),)
            )
        ]

    def exists_guid(self, feed_source_id: UUID, guid_hash: str) -> bool:
        row = self._fetchone(
            "SELECT id FROM feed_items WHERE feed_source_id = ? AND guid_hash = ?",
            (str(feed_source_id), guid_hash),
        )
        return row is not None


class SqliteItemsRepo(SqliteRepo):
    def add(self, record: Item) -> None:
        url_hash = record.canonical_url_hash or canonical_url_hash(record.canonical_url)
        self._execute(
            """
            INSERT OR REPLACE INTO items (id, canonical_url, canonical_url_hash, first_seen_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(record.id),
                record.canonical_url,
                url_hash,
                _to_iso(record.first_seen_at),
            ),
        )

    def get(self, record_id: UUID) -> Item | None:
        row = self._fetchone("SELECT * FROM items WHERE id = ?", (str(record_id),))
        return _row_to_item(row)

    def list_all(self) -> list[Item]:
        return [_row_to_item(row) for row in self._fetchall("SELECT * FROM items")]

    def find_by_hash(self, url_hash: str) -> Item | None:
        row = self._fetchone("SELECT * FROM items WHERE canonical_url_hash = ?", (url_hash,))
        return _row_to_item(row)


class SqliteGroupItemsRepo(SqliteRepo):
    def add_if_new(self, record: GroupItem) -> bool:
        cursor = self._db.connection.execute(
            """
            INSERT OR IGNORE INTO group_items (id, group_id, item_id, first_seen_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                str(record.item_id) if record.item_id else None,
                _to_iso(record.first_seen_at),
            ),
        )
        self._db.connection.commit()
        return cursor.rowcount > 0

    def list_by_group(self, group_id: UUID) -> list[GroupItem]:
        return [
            _row_to_group_item(row)
            for row in self._fetchall(
                "SELECT * FROM group_items WHERE group_id = ?", (str(group_id),)
            )
        ]

    def list_since(self, group_id: UUID, since: datetime) -> list[GroupItem]:
        return [
            _row_to_group_item(row)
            for row in self._fetchall(
                "SELECT * FROM group_items WHERE group_id = ? AND first_seen_at >= ?",
                (str(group_id), _to_iso(since)),
            )
        ]


class SqliteItemEvaluationsRepo(SqliteRepo):
    def add(self, record: ItemEvaluation) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO item_evaluations (
                id, group_id, item_id, relevance_score, decision, reason
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                str(record.item_id) if record.item_id else None,
                record.relevance_score,
                record.decision,
                record.reason,
            ),
        )

    def list_all(self) -> list[ItemEvaluation]:
        return [
            _row_to_evaluation(row)
            for row in self._fetchall("SELECT * FROM item_evaluations")
        ]

    def list_by_group(self, group_id: UUID) -> list[ItemEvaluation]:
        return [
            _row_to_evaluation(row)
            for row in self._fetchall(
                "SELECT * FROM item_evaluations WHERE group_id = ?", (str(group_id),)
            )
        ]

    def find(self, group_id: UUID, item_id: UUID | None) -> ItemEvaluation | None:
        if item_id is None:
            return None
        row = self._fetchone(
            "SELECT * FROM item_evaluations WHERE group_id = ? AND item_id = ?",
            (str(group_id), str(item_id)),
        )
        return _row_to_evaluation(row)


class SqliteItemSummariesRepo(SqliteRepo):
    def add(self, record: ItemSummary) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO item_summaries (id, group_id, item_id, summary_md)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                str(record.item_id) if record.item_id else None,
                record.summary_md,
            ),
        )

    def list_all(self) -> list[ItemSummary]:
        return [_row_to_summary(row) for row in self._fetchall("SELECT * FROM item_summaries")]

    def list_by_group(self, group_id: UUID) -> list[ItemSummary]:
        return [
            _row_to_summary(row)
            for row in self._fetchall(
                "SELECT * FROM item_summaries WHERE group_id = ?", (str(group_id),)
            )
        ]

    def find(self, group_id: UUID, item_id: UUID | None) -> ItemSummary | None:
        if item_id is None:
            return None
        row = self._fetchone(
            "SELECT * FROM item_summaries WHERE group_id = ? AND item_id = ?",
            (str(group_id), str(item_id)),
        )
        return _row_to_summary(row)


class SqliteDigestsRepo(SqliteRepo):
    def add(self, record: Digest) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO digests (id, group_id, scheduled_at, markdown_body, storage_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                _to_iso(record.scheduled_at),
                record.markdown_body,
                record.storage_path,
            ),
        )

    def get(self, record_id: UUID) -> Digest | None:
        row = self._fetchone("SELECT * FROM digests WHERE id = ?", (str(record_id),))
        return _row_to_digest(row)

    def list_all(self) -> list[Digest]:
        return [_row_to_digest(row) for row in self._fetchall("SELECT * FROM digests")]

    def list_by_group(self, group_id: UUID) -> list[Digest]:
        return [
            _row_to_digest(row)
            for row in self._fetchall(
                "SELECT * FROM digests WHERE group_id = ?", (str(group_id),)
            )
        ]


class SqliteDeliveriesRepo(SqliteRepo):
    def add(self, record: Delivery) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO deliveries (id, digest_id, destination_id, status, error_message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.digest_id) if record.digest_id else None,
                str(record.destination_id) if record.destination_id else None,
                record.status,
                record.error_message,
            ),
        )

    def list_all(self) -> list[Delivery]:
        return [_row_to_delivery(row) for row in self._fetchall("SELECT * FROM deliveries")]

    def list_by_digest(self, digest_id: UUID) -> list[Delivery]:
        return [
            _row_to_delivery(row)
            for row in self._fetchall(
                "SELECT * FROM deliveries WHERE digest_id = ?", (str(digest_id),)
            )
        ]


class SqliteJobRunsRepo(SqliteRepo):
    def add(self, record: JobRun) -> None:
        self._execute(
            """
            INSERT OR REPLACE INTO job_runs (
                id, group_id, job_type, status, started_at, finished_at, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.group_id) if record.group_id else None,
                record.job_type,
                record.status,
                _to_iso(record.started_at),
                _to_iso(record.finished_at),
                record.error_message,
            ),
        )

    def list_all(self) -> list[JobRun]:
        return [_row_to_job_run(row) for row in self._fetchall("SELECT * FROM job_runs")]

    def list_by_group(self, group_id: UUID) -> list[JobRun]:
        return [
            _row_to_job_run(row)
            for row in self._fetchall(
                "SELECT * FROM job_runs WHERE group_id = ?", (str(group_id),)
            )
        ]


def _row_to_user(row: sqlite3.Row | None) -> User | None:
    if row is None:
        return None
    return User(
        id=UUID(row["id"]),
        email=row["email"],
        name=row["name"],
        is_admin=bool(row["is_admin"]),
        timezone=row["timezone"],
    )


def _row_to_group(row: sqlite3.Row | None) -> Group | None:
    if row is None:
        return None
    return Group(
        id=UUID(row["id"]),
        user_id=UUID(row["user_id"]) if row["user_id"] else None,
        name=row["name"],
        description=row["description"] or "",
        is_enabled=bool(row["is_enabled"]),
        last_run_started_at=_from_iso(row["last_run_started_at"]),
        last_run_completed_at=_from_iso(row["last_run_completed_at"]),
    )


def _row_to_schedule(row: sqlite3.Row | None) -> GroupSchedule | None:
    if row is None:
        return None
    return GroupSchedule(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        time_hhmm=row["time_hhmm"],
        enabled=bool(row["enabled"]),
        last_fired_at=_from_iso(row["last_fired_at"]),
    )


def _row_to_destination(row: sqlite3.Row | None) -> GroupDestination | None:
    if row is None:
        return None
    return GroupDestination(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        type=row["type"],
        destination=row["destination"],
        token_enc=row["token_enc"],
        enabled=bool(row["enabled"]),
    )


def _row_to_feed_source(row: sqlite3.Row | None) -> FeedSource | None:
    if row is None:
        return None
    return FeedSource(
        id=UUID(row["id"]),
        url=row["url"],
        etag=row["etag"],
        last_modified=row["last_modified"],
        last_fetch_at=_from_iso(row["last_fetch_at"]),
        health_status=row["health_status"],
        consecutive_failures=row["consecutive_failures"] or 0,
        fetch_count=row["fetch_count"] or 0,
        not_modified_count=row["not_modified_count"] or 0,
        failure_count=row["failure_count"] or 0,
    )


def _row_to_group_feed(row: sqlite3.Row | None) -> GroupFeed | None:
    if row is None:
        return None
    return GroupFeed(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        feed_source_id=UUID(row["feed_source_id"]) if row["feed_source_id"] else None,
        enabled=bool(row["enabled"]),
    )


def _row_to_feed_item(row: sqlite3.Row | None) -> FeedItem | None:
    if row is None:
        return None
    return FeedItem(
        id=UUID(row["id"]),
        feed_source_id=UUID(row["feed_source_id"]) if row["feed_source_id"] else None,
        guid_hash=row["guid_hash"],
        url=row["url"],
        published_at=_from_iso(row["published_at"]),
        canonical_url_hash=row["canonical_url_hash"] or "",
    )


def _row_to_item(row: sqlite3.Row | None) -> Item | None:
    if row is None:
        return None
    return Item(
        id=UUID(row["id"]),
        canonical_url=row["canonical_url"],
        canonical_url_hash=row["canonical_url_hash"] or "",
        first_seen_at=_from_iso(row["first_seen_at"]) or datetime.utcnow(),
    )


def _row_to_group_item(row: sqlite3.Row | None) -> GroupItem | None:
    if row is None:
        return None
    return GroupItem(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        item_id=UUID(row["item_id"]) if row["item_id"] else None,
        first_seen_at=_from_iso(row["first_seen_at"]) or datetime.utcnow(),
    )


def _row_to_evaluation(row: sqlite3.Row | None) -> ItemEvaluation | None:
    if row is None:
        return None
    return ItemEvaluation(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        item_id=UUID(row["item_id"]) if row["item_id"] else None,
        relevance_score=row["relevance_score"] or 0.0,
        decision=row["decision"] or "exclude",
        reason=row["reason"] or "",
    )


def _row_to_summary(row: sqlite3.Row | None) -> ItemSummary | None:
    if row is None:
        return None
    return ItemSummary(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        item_id=UUID(row["item_id"]) if row["item_id"] else None,
        summary_md=row["summary_md"] or "",
    )


def _row_to_digest(row: sqlite3.Row | None) -> Digest | None:
    if row is None:
        return None
    return Digest(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        scheduled_at=_from_iso(row["scheduled_at"]),
        markdown_body=row["markdown_body"] or "",
        storage_path=row["storage_path"] or "",
    )


def _row_to_delivery(row: sqlite3.Row | None) -> Delivery | None:
    if row is None:
        return None
    return Delivery(
        id=UUID(row["id"]),
        digest_id=UUID(row["digest_id"]) if row["digest_id"] else None,
        destination_id=UUID(row["destination_id"]) if row["destination_id"] else None,
        status=row["status"] or "pending",
        error_message=row["error_message"],
    )


def _row_to_job_run(row: sqlite3.Row | None) -> JobRun | None:
    if row is None:
        return None
    return JobRun(
        id=UUID(row["id"]),
        group_id=UUID(row["group_id"]) if row["group_id"] else None,
        job_type=row["job_type"] or "",
        status=row["status"] or "pending",
        started_at=_from_iso(row["started_at"]) or datetime.utcnow(),
        finished_at=_from_iso(row["finished_at"]),
        error_message=row["error_message"],
    )
