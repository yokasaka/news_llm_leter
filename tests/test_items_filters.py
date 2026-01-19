from datetime import datetime, timezone

from fastapi.testclient import TestClient

from rss_digest.api.main import create_app
from rss_digest.models import Group, GroupItem, Item, ItemEvaluation, User
from rss_digest.repository import Repositories


def test_items_filter_by_date_range():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    group = Group(user_id=user.id, name="Daily")
    repos.users.add(user)
    repos.groups.add(group)

    early = datetime(2024, 1, 1, tzinfo=timezone.utc)
    late = datetime(2024, 1, 2, tzinfo=timezone.utc)
    item_early = Item(canonical_url="https://example.com/1")
    item_late = Item(canonical_url="https://example.com/2")
    repos.items.add(item_early)
    repos.items.add(item_late)
    repos.group_items.add(GroupItem(group_id=group.id, item_id=item_early.id, first_seen_at=early))
    repos.group_items.add(GroupItem(group_id=group.id, item_id=item_late.id, first_seen_at=late))
    repos.evaluations.add(
        ItemEvaluation(group_id=group.id, item_id=item_late.id, decision="include")
    )

    app = create_app(repositories=repos)
    client = TestClient(app)
    token = client.post(
        "/auth/login",
        json={"email": user.email, "password": "password"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/groups/{group.id}/items",
        params={"from": "2024-01-02T00:00:00+00:00", "to": "2024-01-03T00:00:00+00:00"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["canonical_url"] == "https://example.com/2"
