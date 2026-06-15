from tests.helpers import (
    api_ok,
    approve_through_director,
    auth,
    create_and_submit_reservation,
)


def test_resource_status_tracks_experiment_lifecycle(
    client, student_token, teacher_token, director_token, admin_token, ids
):
    rid = create_and_submit_reservation(
        client,
        student_token,
        ids["teacher_id"],
        ids["pool_id"],
        exp_name="资源状态测试",
        days_ahead=55,
    )
    detail = approve_through_director(client, rid, teacher_token, director_token)
    task_id = detail["experimentTaskId"]

    pool = api_ok(client.get(f"/api/resources/{ids['pool_id']}", headers=auth(admin_token)))
    assert pool["status"] == "RESERVED"

    api_ok(client.post(f"/api/experiments/{task_id}/ready", headers=auth(admin_token)))
    pool = api_ok(client.get(f"/api/resources/{ids['pool_id']}", headers=auth(admin_token)))
    assert pool["status"] == "RESERVED"

    api_ok(client.post(f"/api/experiments/{task_id}/start", headers=auth(admin_token)))
    pool = api_ok(client.get(f"/api/resources/{ids['pool_id']}", headers=auth(admin_token)))
    assert pool["status"] == "IN_USE"

    api_ok(client.post(f"/api/experiments/{task_id}/finish", headers=auth(admin_token)))
    pool = api_ok(client.get(f"/api/resources/{ids['pool_id']}", headers=auth(admin_token)))
    assert pool["status"] == "AVAILABLE"
