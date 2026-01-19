"""Item endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from rss_digest.api.dependencies import get_current_user, get_repositories
from rss_digest.api.routers.helpers import get_group_or_404
from rss_digest.api.schemas import ItemResponse
from rss_digest.db.models import User
from rss_digest.repository import Repositories

router = APIRouter(prefix="/groups/{group_id}/items", tags=["items"])


@router.get("", response_model=list[ItemResponse])
def list_items(
    group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    repos: Annotated[Repositories, Depends(get_repositories)],
    decision: str = "all",
) -> list[ItemResponse]:
    group = get_group_or_404(repos, group_id, current_user)
    group_items = repos.group_items.list_by_group(group.id)
    evaluations = {eval_.item_id: eval_ for eval_ in repos.evaluations.list_by_group(group.id)}
    summaries = {summary.item_id: summary for summary in repos.summaries.list_by_group(group.id)}
    items: list[ItemResponse] = []
    for group_item in group_items:
        item = repos.items.get(group_item.item_id)
        if item is None:
            continue
        evaluation = evaluations.get(item.id)
        if decision != "all":
            if evaluation is None or evaluation.decision != decision:
                continue
        summary = summaries.get(item.id)
        items.append(
            ItemResponse(
                id=item.id,
                canonical_url=item.canonical_url,
                first_seen_at=item.first_seen_at,
                decision=evaluation.decision if evaluation else None,
                summary_md=summary.summary_md if summary else None,
            )
        )
    return items
