from tests.helpers import (
    api_ok,
    approve_through_director,
    auth,
    create_and_submit_reservation,
    reservation_payload,
)


def test_create_reservation_with_master_detail(
    client, student_token, ids
):
    payload = reservation_payload(
        ids["teacher_id"],
        ids["pool_id"],
        extra_resource_id=ids["ship_id"],
        exp_name="主从表示例验",
    )
    created = api_ok(
        client.post("/api/reservations", json=payload, headers=auth(student_token))
    )
    assert created["status"] == "DRAFT"
    assert len(created["resources"]) == 2
    assert created["resources"][0]["resourceId"] == ids["pool_id"]
    assert created["resources"][1]["resourceId"] == ids["ship_id"]

    detail = api_ok(
        client.get(f"/api/reservations/{created['id']}", headers=auth(student_token))
    )
    assert detail["expName"] == "主从表示例验"
    assert len(detail["resources"]) == 2


def test_submit_and_teacher_director_approval(
    client, student_token, teacher_token, director_token, ids
):
    rid = create_and_submit_reservation(
        client,
        student_token,
        ids["teacher_id"],
        ids["pool_id"],
        ids["ship_id"],
        exp_name="审批链测试",
        days_ahead=20,
    )
    submitted = api_ok(client.get(f"/api/reservations/{rid}", headers=auth(student_token)))
    assert submitted["status"] == "PENDING_TEACHER"

    detail = approve_through_director(client, rid, teacher_token, director_token)
    assert detail["experimentTaskId"]
    assert len(detail["approvalLogs"]) == 2
    steps = {log["stepType"] for log in detail["approvalLogs"]}
    assert steps == {"TEACHER_REVIEW", "DIRECTOR_APPROVAL"}


def test_resource_conflict_detection(client, student_token, ids):
    create_and_submit_reservation(
        client,
        student_token,
        ids["teacher_id"],
        ids["pool_id"],
        exp_name="已占用预约",
        days_ahead=30,
    )

    payload = reservation_payload(
        ids["teacher_id"],
        ids["pool_id"],
        exp_name="冲突预约",
        days_ahead=30,
    )
    created = api_ok(
        client.post("/api/reservations", json=payload, headers=auth(student_token))
    )
    conflict = api_ok(
        client.post(
            f"/api/reservations/{created['id']}/check-conflicts",
            headers=auth(student_token),
        )
    )
    assert conflict["hasConflict"] is True
    assert len(conflict["conflicts"]) >= 1
    assert conflict["conflicts"][0]["resourceId"] == ids["pool_id"]


def test_teacher_reject_requires_comment(client, student_token, teacher_token, ids):
    rid = create_and_submit_reservation(
        client,
        student_token,
        ids["teacher_id"],
        ids["pool_id"],
        days_ahead=40,
    )
    resp = client.post(
        f"/api/reservations/{rid}/teacher-review",
        json={"approved": False, "comment": ""},
        headers=auth(teacher_token),
    )
    assert resp.status_code == 200
    assert resp.json()["code"] != 200
