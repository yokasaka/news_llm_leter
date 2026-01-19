"""Database session management."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./rss_digest.db")


def build_engine():
    url = _database_url()
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(url, future=True, connect_args=connect_args)


def build_session_factory() -> sessionmaker[Session]:
    engine = build_engine()
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

