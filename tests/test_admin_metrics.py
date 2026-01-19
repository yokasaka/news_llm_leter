from datetime import datetime, timezone

from fastapi.testclient import TestClient

from rss_digest.api.main import create_app
from rss_digest.models import (
    Delivery,
    Digest,
    FeedSource,
    Group,
    ItemEvaluation,
    ItemSummary,
    User,
)
from rss_digest.repository import Repositories


def test_admin_metrics_summary():
    repos = Repositories.build()
    admin = User(email="admin@example.com", timezone="UTC", is_admin=True)
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(admin)
    repos.users.add(user)
    group = Group(user_id=user.id, name="Daily")
    repos.groups.add(group)
    feed_source = FeedSource(
        url="https://example.com/rss",
        fetch_count=10,
        not_modified_count=4,
        failure_count=2,
    )
    repos.feed_sources.add(feed_source)
    digest = Digest(group_id=group.id, scheduled_at=datetime.now(timezone.utc))
    repos.digests.add(digest)
    repos.deliveries.add(
        Delivery(digest_id=digest.id, destination_id=None, status="sent")
    )
    repos.evaluations.add(
        ItemEvaluation(group_id=group.id, item_id=None, decision="include")
    )
    repos.summaries.add(ItemSummary(group_id=group.id, item_id=None, summary_md="sum"))

    app = create_app(repositories=repos)
    client = TestClient(app)
    token = client.post(
        "/auth/login",
        json={"email": admin.email, "password": "password"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/admin/metrics", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["active_users"] == 1
    assert data["feed_not_modified_rate"] == 0.4
    assert data["feed_failure_rate"] == 0.2
    assert data["delivery_failure_rate"] == 0.0
    assert data["llm_evaluations"] == 1
    assert data["llm_summaries"] == 1
