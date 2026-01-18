"""Authentication endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rss_digest.api.dependencies import get_current_user, get_repositories
from rss_digest.api.routers.helpers import user_response
from rss_digest.api.schemas import LoginRequest, TokenResponse, UserResponse
from rss_digest.models import User
from rss_digest.repository import Repositories

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, repos: Annotated[Repositories, Depends(get_repositories)]
) -> TokenResponse:
    user = repos.users.find_by_email(payload.email)
    if user is None or payload.password != "password":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=user.email)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return user_response(current_user)
