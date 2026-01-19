"""Initial schema.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-01-18 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "groups",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_started_at", sa.DateTime(timezone=True)),
        sa.Column("last_run_completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "group_schedules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id"),
            nullable=False,
        ),
        sa.Column("time_hhmm", sa.String(length=5), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_fired_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("group_id", "time_hhmm", name="uq_group_schedules_time"),
    )

    op.create_table(
        "group_destinations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("destination", sa.Text(), nullable=False),
        sa.Column("token_enc", sa.Text()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "feed_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("etag", sa.Text()),
        sa.Column("last_modified", sa.Text()),
        sa.Column("last_fetch_at", sa.DateTime(timezone=True)),
        sa.Column("health_status", sa.String(length=32), nullable=False, server_default="healthy"),
        sa.Column(
            "consecutive_failures", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.UniqueConstraint("url", name="uq_feed_sources_url"),
    )

    op.create_table(
        "group_feeds",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id"),
            nullable=False,
        ),
        sa.Column(
            "feed_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("feed_sources.id"),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("group_id", "feed_source_id", name="uq_group_feeds_source"),
    )

    op.create_table(
        "feed_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "feed_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("feed_sources.id"),
            nullable=False,
        ),
        sa.Column("guid_hash", sa.String(length=128), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("canonical_url_hash", sa.String(length=128), nullable=False),
        sa.UniqueConstraint("feed_source_id", "guid_hash", name="uq_feed_items_guid"),
    )

    op.create_table(
        "items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("canonical_url_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("canonical_url_hash", name="uq_items_canonical"),
    )

    op.create_table(
        "group_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id"),
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("group_id", "item_id", name="uq_group_items_item"),
    )

    op.create_table(
        "item_evaluations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id"),
            nullable=False,
        ),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("decision", sa.String(length=32), nullable=False, server_default="exclude"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("group_id", "item_id", name="uq_item_evaluations_item"),
    )

    op.create_table(
        "item_summaries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id"),
            nullable=False,
        ),
        sa.Column("summary_md", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("group_id", "item_id", name="uq_item_summaries_item"),
    )

    op.create_table(
        "digests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("groups.id"),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("markdown_body", sa.Text(), nullable=False, server_default=""),
        sa.Column("storage_path", sa.Text(), nullable=False, server_default=""),
    )

    op.create_table(
        "deliveries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "digest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("digests.id"),
            nullable=False,
        ),
        sa.Column(
            "destination_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("group_destinations.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("deliveries")
    op.drop_table("digests")
    op.drop_table("item_summaries")
    op.drop_table("item_evaluations")
    op.drop_table("group_items")
    op.drop_table("items")
    op.drop_table("feed_items")
    op.drop_table("group_feeds")
    op.drop_table("feed_sources")
    op.drop_table("group_destinations")
    op.drop_table("group_schedules")
    op.drop_table("groups")
    op.drop_table("users")
