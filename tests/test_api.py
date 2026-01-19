from fastapi.testclient import TestClient

from rss_digest.api.main import create_app
from rss_digest.db.models import User


def test_group_crud_flow(repositories):
    repos = repositories
    user = repos.users.add(User(email="user@example.com", timezone="UTC"))
    app = create_app(repositories=repos)
    client = TestClient(app)

    login_response = client.post(
        "/auth/login", json={"email": user.email, "password": "password"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    create_response = client.post(
        "/groups", json={"name": "Daily", "description": "News"}, headers=headers
    )
    assert create_response.status_code == 200
    group_id = create_response.json()["id"]

    list_response = client.get("/groups", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/groups/{group_id}", json={"is_enabled": False}, headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_enabled"] is False

    delete_response = client.delete(f"/groups/{group_id}", headers=headers)
    assert delete_response.status_code == 200
