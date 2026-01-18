"""FastAPI entrypoint for the RSS digest backend."""

from __future__ import annotations

from fastapi import FastAPI

from rss_digest.api.routers import admin, auth, destinations, digests, feeds, groups, items, schedules
from rss_digest.models import User
from rss_digest.repository import Repositories


def create_app(repositories: Repositories | None = None) -> FastAPI:
    app = FastAPI()
    app.state.repositories = repositories or _build_default_repositories()

    app.include_router(auth.router)
    app.include_router(groups.router)
    app.include_router(feeds.router)
    app.include_router(schedules.router)
    app.include_router(destinations.router)
    app.include_router(items.router)
    app.include_router(digests.router)
    app.include_router(admin.router)

    return app


def _build_default_repositories() -> Repositories:
    repos = Repositories.build()
    admin_user = User(
        email="admin@example.com",
        name="Admin",
        is_admin=True,
        timezone="UTC",
    )
    repos.users.add(admin_user)
    return repos
