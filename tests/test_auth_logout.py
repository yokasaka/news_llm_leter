from fastapi.testclient import TestClient

from rss_digest.api.main import create_app
from rss_digest.models import User
from rss_digest.repository import Repositories


def test_logout_clears_session():
    repos = Repositories.build()
    user = User(email="user@example.com", timezone="UTC")
    repos.users.add(user)
    app = create_app(repositories=repos)
    client = TestClient(app)

    token = client.post(
        "/auth/login",
        json={"email": user.email, "password": "password"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/auth/logout", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "logged_out"
