"""API dependencies for repositories and authentication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from sqlalchemy.orm import Session

from rss_digest.db.models import User
from rss_digest.db.session import build_session_factory
from rss_digest.repository import Repositories


@dataclass
class AuthResult:
    user: User


def get_session(request: Request) -> Session | None:
    if getattr(request.app.state, "repositories", None) is not None:
        yield None
        return
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        session_factory = build_session_factory()
        request.app.state.session_factory = session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_repositories(
    request: Request, session: Annotated[Session | None, Depends(get_session)]
) -> Repositories:
    repositories = getattr(request.app.state, "repositories", None)
    if repositories is not None:
        return repositories
    if session is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB session missing")
    return Repositories.build(session=session)


def get_current_user(
    repositories: Annotated[Repositories, Depends(get_repositories)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    token = parts[1]
    user = repositories.users.find_by_email(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user
