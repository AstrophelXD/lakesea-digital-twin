from tests.helpers import api_ok, auth, login


def test_login_success(client):
    data = api_ok(client.post("/api/auth/login", json={"username": "admin", "password": "123456"}))
    assert data["token"]
    assert data["user"]["username"] == "admin"
    assert "ADMIN" in data["user"]["roles"]


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 200
    assert resp.json()["code"] != 200


def test_profile_has_menus(client, student_token):
    data = api_ok(client.get("/api/auth/profile", headers=auth(student_token)))
    assert data["user"]["username"] == "student01"
    assert "reservations" in data["menus"]


def test_student_cannot_list_users(client, student_token):
    resp = client.get("/api/users", headers=auth(student_token))
    assert resp.status_code == 200
    assert resp.json()["code"] == 403
