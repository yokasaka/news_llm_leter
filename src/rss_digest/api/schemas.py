"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    is_admin: bool
    timezone: str


class GroupCreateRequest(BaseModel):
    name: str
    description: str | None = None


class GroupUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None


class GroupResponse(BaseModel):
    id: UUID
    name: str
    description: str
    is_enabled: bool
    last_run_started_at: datetime | None = None
    last_run_completed_at: datetime | None = None


class FeedAddRequest(BaseModel):
    feed_url: str


class FeedDiscoverRequest(BaseModel):
    site_url: str


class FeedCandidateResponse(BaseModel):
    url: str
    type: str
    title: str | None = None


class GroupFeedResponse(BaseModel):
    id: UUID
    feed_source_id: UUID
    feed_url: str
    enabled: bool


class GroupFeedUpdateRequest(BaseModel):
    enabled: bool


class ScheduleCreateRequest(BaseModel):
    time_hhmm: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class ScheduleUpdateRequest(BaseModel):
    time_hhmm: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    enabled: bool | None = None


class ScheduleResponse(BaseModel):
    id: UUID
    time_hhmm: str
    enabled: bool
    last_fired_at: datetime | None = None


class DestinationCreateRequest(BaseModel):
    type: Literal["email", "slack"] = "email"
    destination: str
    token: str | None = None


class DestinationUpdateRequest(BaseModel):
    enabled: bool | None = None


class DestinationResponse(BaseModel):
    id: UUID
    type: str
    destination: str
    enabled: bool


class ItemResponse(BaseModel):
    id: UUID
    canonical_url: str
    first_seen_at: datetime
    decision: str | None = None
    summary_md: str | None = None


class DigestResponse(BaseModel):
    id: UUID
    scheduled_at: datetime | None = None
    markdown_body: str
    storage_path: str


class DeliveryResponse(BaseModel):
    id: UUID
    digest_id: UUID
    destination_id: UUID
    status: str
    error_message: str | None = None


class AdminFeedHealthResponse(BaseModel):
    id: UUID
    url: str
    health_status: str
    consecutive_failures: int
    last_fetch_at: datetime | None = None


class JobRunResponse(BaseModel):
    id: UUID
    group_id: UUID | None = None
    job_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    error_message: str | None = None


class AdminUsageResponse(BaseModel):
    total_users: int
    total_groups: int
    total_feed_sources: int
    total_group_feeds: int
    total_digests: int
    total_deliveries: int


class AdminMetricsResponse(BaseModel):
    active_users: int
    feed_not_modified_rate: float
    feed_failure_rate: float
    llm_evaluations: int
    llm_summaries: int
    delivery_failure_rate: float
