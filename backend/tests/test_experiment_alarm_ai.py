from decimal import Decimal

from tests.helpers import (
    api_ok,
    approve_through_director,
    auth,
    create_and_submit_reservation,
    run_experiment_lifecycle,
)


def _approved_archived_task(client, student_token, teacher_token, director_token, admin_token, ids):
    rid = create_and_submit_reservation(
        client,
        student_token,
        ids["teacher_id"],
        ids["pool_id"],
        ids["ship_id"],
        exp_name="试验全链路",
        days_ahead=50,
    )
    detail = approve_through_director(client, rid, teacher_token, director_token)
    task_id = detail["experimentTaskId"]
    run_experiment_lifecycle(client, admin_token, task_id, archive=True)
    return task_id


def test_experiment_lifecycle(client, student_token, teacher_token, director_token, admin_token, ids):
    task_id = _approved_archived_task(
        client, student_token, teacher_token, director_token, admin_token, ids
    )
    task = api_ok(client.get(f"/api/experiments/{task_id}", headers=auth(admin_token)))
    assert task["status"] == "ARCHIVED"


def test_monitor_demo_alarm_and_handle(
    client, student_token, teacher_token, director_token, admin_token, ids
):
    rid = create_and_submit_reservation(
        client,
        student_token,
        ids["teacher_id"],
        ids["pool_id"],
        days_ahead=60,
    )
    detail = approve_through_director(client, rid, teacher_token, director_token)
    task_id = detail["experimentTaskId"]
    api_ok(client.post(f"/api/experiments/{task_id}/ready", headers=auth(admin_token)))
    api_ok(client.post(f"/api/experiments/{task_id}/start", headers=auth(admin_token)))

    frame = api_ok(
        client.post(
            f"/api/monitor/{task_id}/demo-alarm",
            params={"alarmType": "LOW_BATTERY"},
            headers=auth(admin_token),
        )
    )
    assert frame.get("alarm")

    alarms = api_ok(
        client.get(
            "/api/alarms",
            params={"experimentId": task_id},
            headers=auth(director_token),
        )
    )
    assert alarms["total"] >= 1
    alarm_id = alarms["items"][0]["id"]

    handled = api_ok(
        client.post(
            f"/api/alarms/{alarm_id}/handle",
            json={"handleStatus": "RESOLVED", "comment": "pytest 已处理"},
            headers=auth(director_token),
        )
    )
    assert handled["handleStatus"] == "RESOLVED"

    api_ok(client.post(f"/api/experiments/{task_id}/finish", headers=auth(admin_token)))


def test_ai_mode_mock(client, admin_token):
    mode = api_ok(client.get("/api/ai/mode", headers=auth(admin_token)))
    assert mode["analysisMode"] == "Mock"
    assert mode["mockAi"] is True


def test_ai_generate_and_query_report(
    client, student_token, teacher_token, director_token, admin_token, ids
):
    task_id = _approved_archived_task(
        client, student_token, teacher_token, director_token, admin_token, ids
    )

    # 归档试验无传感器时 AI 摘要可能为空，补少量传感器数据
    from app.core.database import SessionLocal
    from app.models.monitor import SensorData
    from datetime import datetime

    db = SessionLocal()
    try:
        db.add(
            SensorData(
                experiment_id=task_id,
                timestamp=datetime.now(),
                position_x=Decimal("10"),
                position_y=Decimal("10"),
                speed=Decimal("1.5"),
                battery=Decimal("80"),
                resistance=Decimal("30"),
            )
        )
        db.commit()
    finally:
        db.close()

    generated = api_ok(
        client.post(
            "/api/ai/reports/generate",
            json={"experimentId": task_id, "analysisType": "OVERVIEW"},
            headers=auth(admin_token),
        )
    )
    assert generated["experimentId"] == task_id
    assert generated["mock"] is True
    assert generated.get("sections") or generated.get("summaryText")

    fetched = api_ok(
        client.get(f"/api/ai/reports/{task_id}", headers=auth(admin_token))
    )
    assert fetched["experimentId"] == task_id

    logs = api_ok(
        client.get("/api/ai/logs", params={"experimentId": task_id}, headers=auth(admin_token))
    )
    assert logs["total"] >= 1
