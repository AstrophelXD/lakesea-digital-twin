from tests.helpers import api_ok, auth


def test_db_health(client):
    data = api_ok(client.get("/api/health/db"))
    assert data["connected"] is True
    assert data["databaseType"] == "SQLite"


def test_dashboard_summary(client, admin_token):
    api_ok(client.get("/api/dashboard/summary", headers=auth(admin_token)))


def test_list_users_admin(client, admin_token):
    data = api_ok(client.get("/api/users", headers=auth(admin_token)))
    assert data["total"] >= 4


def test_list_resources(client, admin_token):
    data = api_ok(client.get("/api/resources", headers=auth(admin_token)))
    assert data["total"] >= 2
