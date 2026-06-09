"""测试辅助函数。"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, username: str, password: str = "123456") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 200, body
    return body["data"]["token"]


def api_ok(resp) -> dict:
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 200, body
    return body["data"]


def reservation_window(days_ahead: int = 10) -> tuple[datetime, datetime]:
    start = datetime.now().replace(microsecond=0) + timedelta(days=days_ahead)
    end = start + timedelta(hours=3)
    return start, end


def reservation_payload(
    teacher_id: int,
    resource_id: int,
    *,
    exp_name: str = "pytest 试验预约",
    days_ahead: int = 10,
    extra_resource_id: int | None = None,
) -> dict:
    start, end = reservation_window(days_ahead)
    resources = [
        {
            "resourceId": resource_id,
            "resourceType": "POOL",
            "quantity": 1,
            "startTime": start.isoformat(),
            "endTime": end.isoformat(),
            "remark": "主资源",
        }
    ]
    if extra_resource_id:
        resources.append(
            {
                "resourceId": extra_resource_id,
                "resourceType": "SHIP",
                "quantity": 1,
                "startTime": start.isoformat(),
                "endTime": end.isoformat(),
                "remark": "从表资源",
            }
        )
    return {
        "expName": exp_name,
        "expType": "集成测试",
        "teacherId": teacher_id,
        "startTime": start.isoformat(),
        "endTime": end.isoformat(),
        "purpose": "pytest 自动化",
        "planSummary": "主从表 + 审批链",
        "resources": resources,
    }


def create_and_submit_reservation(
    client: TestClient,
    student_token: str,
    teacher_id: int,
    pool_id: int,
    ship_id: int | None = None,
    *,
    exp_name: str = "pytest 试验预约",
    days_ahead: int = 10,
) -> int:
    payload = reservation_payload(
        teacher_id,
        pool_id,
        exp_name=exp_name,
        days_ahead=days_ahead,
        extra_resource_id=ship_id,
    )
    created = api_ok(
        client.post("/api/reservations", json=payload, headers=auth(student_token))
    )
    rid = created["id"]
    api_ok(client.post(f"/api/reservations/{rid}/submit", headers=auth(student_token)))
    return rid


def approve_through_director(
    client: TestClient,
    reservation_id: int,
    teacher_token: str,
    director_token: str,
) -> dict:
    detail = api_ok(
        client.post(
            f"/api/reservations/{reservation_id}/teacher-review",
            json={"approved": True, "comment": "教师通过"},
            headers=auth(teacher_token),
        )
    )
    assert detail["status"] == "PENDING_DIRECTOR"
    detail = api_ok(
        client.post(
            f"/api/reservations/{reservation_id}/director-approve",
            json={"approved": True, "comment": "主任批准"},
            headers=auth(director_token),
        )
    )
    assert detail["status"] == "APPROVED"
    assert detail.get("experimentTaskId")
    return detail


def run_experiment_lifecycle(
    client: TestClient,
    admin_token: str,
    task_id: int,
    *,
    archive: bool = True,
) -> None:
    api_ok(client.post(f"/api/experiments/{task_id}/ready", headers=auth(admin_token)))
    api_ok(client.post(f"/api/experiments/{task_id}/start", headers=auth(admin_token)))
    api_ok(client.post(f"/api/experiments/{task_id}/finish", headers=auth(admin_token)))
    if archive:
        api_ok(client.post(f"/api/experiments/{task_id}/archive", headers=auth(admin_token)))
