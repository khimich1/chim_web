"""IDOR: teacher B cannot cancel/restore teacher A homework."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.multi_teacher.conftest import (
    TEACHER_A_EMAIL,
    TEACHER_B_EMAIL,
    mt_login,
    mt_logout,
)


def test_teacher_b_cannot_cancel_or_restore_teacher_a_homework(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    created = client.post(
        "/api/homework",
        json={
            "student_id": client.student_a_id,
            "title": "Teacher A HW",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert created.status_code == 201
    assignment_id = created.json()["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    assert (
        client.post(f"/api/homework/{assignment_id}/cancel", json={}).status_code
        in (403, 404)
    )
    assert (
        client.post(f"/api/homework/{assignment_id}/restore", json={}).status_code
        in (403, 404)
    )


def test_teacher_b_cannot_wave_cancel_teacher_a_batch(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    group = client.post("/api/teacher/groups", json={"name": "A-group"}).json()
    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [client.student_a_id]},
        ).status_code
        == 200
    )
    template = client.post(
        "/api/homework/templates",
        json={
            "title": "Wave A",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    ).json()
    assigned = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"group_id": group["id"]},
    )
    assert assigned.status_code == 201
    anchor_id = assigned.json()[0]["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    assert (
        client.post(
            f"/api/homework/{anchor_id}/cancel",
            json={"scope": "wave"},
        ).status_code
        in (403, 404)
    )
    assert (
        client.post(
            f"/api/homework/{anchor_id}/restore",
            json={"scope": "wave"},
        ).status_code
        in (403, 404)
    )
