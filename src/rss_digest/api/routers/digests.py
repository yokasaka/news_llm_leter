"""Digest endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from rss_digest.api.dependencies import get_current_user, get_repositories
from rss_digest.api.routers.helpers import digest_response, get_group_or_404
from rss_digest.api.schemas import DigestResponse
from rss_digest.models import User
from rss_digest.repository import Repositories

router = APIRouter(tags=["digests"])


@router.get("/groups/{group_id}/digests", response_model=list[DigestResponse])
def list_digests(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> list[DigestResponse]:
    group = get_group_or_404(repos, group_id, current_user)
    digests = repos.digests.list_by_group(group.id)
    return [digest_response(digest) for digest in digests]


@router.get("/digests/{digest_id}", response_model=DigestResponse)
def get_digest(
    digest_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> DigestResponse:
    _ = current_user
    digest = repos.digests.get(digest_id)
    if digest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found")
    return digest_response(digest)


@router.get("/digests/{digest_id}/download")
def download_digest(
    digest_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
) -> FileResponse:
    _ = current_user
    digest = repos.digests.get(digest_id)
    if digest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found")
    path = Path(digest.storage_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(path)
