from datetime import datetime, timezone

from fastapi.testclient import TestClient

from rss_digest.api.main import create_app
from rss_digest.models import (
    Delivery,
    Digest,
    FeedSource,
    Group,
    GroupDestination,
    GroupFeed,
    JobRun,
    User,
)
from rss_digest.repository import Repositories


def _build_client(repos: Repositories) -> TestClient:
    app = create_app(repositories=repos)
    return TestClient(app)


def _login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": "password"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_usage_requires_admin():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(user)
    client = _build_client(repos)

    headers = _login(client, user.email)
    response = client.get("/admin/usage", headers=headers)

    assert response.status_code == 403


def test_admin_users_requires_admin():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(user)
    client = _build_client(repos)

    headers = _login(client, user.email)
    response = client.get("/admin/users", headers=headers)

    assert response.status_code == 403


def test_admin_usage_counts():
    repos = Repositories.build()
    admin = User(email="admin@example.com", timezone="UTC", is_admin=True)
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(admin)
    repos.users.add(user)
    group = Group(user_id=user.id, name="Daily")
    repos.groups.add(group)
    feed_source = FeedSource(url="https://example.com/rss")
    repos.feed_sources.add(feed_source)
    repos.group_feeds.add(GroupFeed(group_id=group.id, feed_source_id=feed_source.id))
    digest = Digest(group_id=group.id, markdown_body="digest")
    repos.digests.add(digest)
    destination = GroupDestination(group_id=group.id, destination="user@example.com")
    repos.destinations.add(destination)
    repos.deliveries.add(
        Delivery(digest_id=digest.id, destination_id=destination.id, status="sent")
    )
    client = _build_client(repos)

    headers = _login(client, admin.email)
    response = client.get("/admin/usage", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 2
    assert data["total_groups"] == 1
    assert data["total_feed_sources"] == 1
    assert data["total_group_feeds"] == 1
    assert data["total_digests"] == 1
    assert data["total_deliveries"] == 1


def test_admin_feed_health():
    repos = Repositories.build()
    admin = User(email="admin@example.com", timezone="UTC", is_admin=True)
    repos.users.add(admin)
    fetched_at = datetime(2024, 1, 2, 3, 4, tzinfo=timezone.utc)
    repos.feed_sources.add(
        FeedSource(
            url="https://example.com/rss",
            health_status="degraded",
            consecutive_failures=2,
            last_fetch_at=fetched_at,
        )
    )
    client = _build_client(repos)

    headers = _login(client, admin.email)
    response = client.get("/admin/feeds", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data[0]["url"] == "https://example.com/rss"
    assert data[0]["health_status"] == "degraded"
    assert data[0]["consecutive_failures"] == 2
    returned = datetime.fromisoformat(data[0]["last_fetch_at"].replace("Z", "+00:00"))
    assert returned == fetched_at


def test_admin_feed_health_requires_admin():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(user)
    client = _build_client(repos)

    headers = _login(client, user.email)
    response = client.get("/admin/feeds", headers=headers)

    assert response.status_code == 403


def test_admin_jobs():
    repos = Repositories.build()
    admin = User(email="admin@example.com", timezone="UTC", is_admin=True)
    repos.users.add(admin)
    job = JobRun(job_type="digest", status="success")
    repos.job_runs.add(job)
    client = _build_client(repos)

    headers = _login(client, admin.email)
    response = client.get("/admin/jobs", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data[0]["job_type"] == "digest"
    assert data[0]["status"] == "success"


def test_admin_jobs_requires_admin():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(user)
    client = _build_client(repos)

    headers = _login(client, user.email)
    response = client.get("/admin/jobs", headers=headers)

    assert response.status_code == 403


def test_admin_deliveries():
    repos = Repositories.build()
    admin = User(email="admin@example.com", timezone="UTC", is_admin=True)
    repos.users.add(admin)
    digest = Digest(markdown_body="digest")
    repos.digests.add(digest)
    destination = GroupDestination(destination="user@example.com")
    repos.destinations.add(destination)
    delivery = Delivery(digest_id=digest.id, destination_id=destination.id, status="sent")
    repos.deliveries.add(delivery)
    client = _build_client(repos)

    headers = _login(client, admin.email)
    response = client.get("/admin/deliveries", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data[0]["digest_id"] == str(digest.id)
    assert data[0]["destination_id"] == str(destination.id)


def test_admin_deliveries_requires_admin():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(user)
    client = _build_client(repos)

    headers = _login(client, user.email)
    response = client.get("/admin/deliveries", headers=headers)

    assert response.status_code == 403
