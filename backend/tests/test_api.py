def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["token"]


def test_db_health(client):
    resp = client.get("/api/health/db")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["connected"] is True
    assert "databaseType" in data


def test_dashboard_summary(client, admin_token):
    resp = client.get("/api/dashboard/summary", headers=_auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["code"] == 200


def test_list_users_admin_only(client, admin_token):
    resp = client.get("/api/users", headers=_auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 2
