"""FastAPI entrypoint for the RSS digest backend."""

from __future__ import annotations

from fastapi import FastAPI

from rss_digest.api.routers import admin, auth, destinations, digests, feeds, groups, items, schedules
from rss_digest.db.models import User
from rss_digest.db.session import build_session_factory
from rss_digest.repository import Repositories


def create_app(repositories: Repositories | None = None) -> FastAPI:
    app = FastAPI()
    if repositories is not None:
        app.state.repositories = repositories
    else:
        session_factory = build_session_factory()
        app.state.session_factory = session_factory
        _ensure_admin_user(session_factory())

    app.include_router(auth.router)
    app.include_router(groups.router)
    app.include_router(feeds.router)
    app.include_router(schedules.router)
    app.include_router(destinations.router)
    app.include_router(items.router)
    app.include_router(digests.router)
    app.include_router(admin.router)

    return app


def _ensure_admin_user(session) -> None:
    repos = Repositories.build(session=session)
    admin_user = repos.users.find_by_email("admin@example.com")
    if admin_user is None:
        admin_user = User(
            email="admin@example.com",
            name="Admin",
            is_admin=True,
            timezone="UTC",
        )
        repos.users.add(admin_user)
    session.close()
