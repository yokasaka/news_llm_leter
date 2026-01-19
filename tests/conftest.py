from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from rss_digest.db.base import Base
from rss_digest.repository import Repositories


@pytest.fixture()
def repositories() -> Iterator[Repositories]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    session = session_factory()
    try:
        yield Repositories.build(session=session)
    finally:
        session.close()
