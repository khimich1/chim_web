"""Multi-teacher isolation (Variant A): teacher A must not access teacher B data.

Checklist: docs/ideas/production-hardening.md § IDOR Audit Checklist.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.multi_teacher.conftest import (
    PNG_BYTES,
    STUDENT_A_EMAIL,
    STUDENT_B_EMAIL,
    TEACHER_A_EMAIL,
    TEACHER_B_EMAIL,
    mt_login,
    mt_logout,
)


def test_teacher_b_cannot_list_teacher_a_students(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    listed_as_a = client.get("/api/students")
    assert listed_as_a.status_code == 200
    assert len(listed_as_a.json()) == 1
    assert listed_as_a.json()[0]["id"] == client.student_a_id

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    listed_as_b = client.get("/api/students")
    assert listed_as_b.status_code == 200
    student_ids = {item["id"] for item in listed_as_b.json()}
    assert client.student_a_id not in student_ids
    assert client.student_b_id in student_ids


def test_teacher_b_cannot_create_homework_for_teacher_a_student(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_B_EMAIL)
    response = client.post(
        "/api/homework",
        json={
            "student_id": client.student_a_id,
            "title": "Cross-tenant homework",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert response.status_code in (403, 404)


def test_teacher_b_cannot_read_teacher_a_homework(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    create = client.post(
        "/api/homework",
        json={
            "student_id": client.student_a_id,
            "title": "Teacher A homework",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert create.status_code == 201
    assignment_id = create.json()["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    assert client.get(f"/api/homework/{assignment_id}").status_code == 403


def test_teacher_b_cannot_read_teacher_a_uploaded_image(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    upload = client.post(
        "/api/uploads/images",
        files={"file": ("diagram.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 201
    image_id = upload.json()["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    assert client.get(f"/api/uploads/images/{image_id}").status_code == 403


def test_student_cannot_read_other_students_uploaded_image(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, STUDENT_A_EMAIL)
    upload = client.post(
        "/api/uploads/images",
        files={"file": ("answer.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 201
    image_id = upload.json()["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    # Teacher B is not owner and has no homework link to this image
    assert client.get(f"/api/uploads/images/{image_id}").status_code == 403


def test_leaderboard_is_global_cross_tenant(
    multi_teacher_client: TestClient,
) -> None:
    """Cross-tenant by design — students from different teachers share one board."""
    client = multi_teacher_client
    mt_login(client, STUDENT_A_EMAIL)
    assert client.get("/api/leaderboard").status_code == 200

    mt_logout(client)
    mt_login(client, STUDENT_B_EMAIL)
    assert client.get("/api/leaderboard").status_code == 200


def _create_theme(client: TestClient) -> dict:
    response = client.post(
        "/api/teacher/themes",
        json={
            "title": "ОВР",
            "description": "Тема A",
            "is_published": False,
            "sort_order": 1,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _submit_lecture_homework(client: TestClient, student_id: str) -> str:
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Лекция A",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert create.status_code == 201, create.text
    assignment_id = create.json()["id"]

    mt_logout(client)
    mt_login(client, STUDENT_A_EMAIL)
    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    return assignment_id


def test_teacher_b_cannot_access_teacher_a_theme(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    theme = _create_theme(client)
    task = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "Q"}],
            "correct_value": "A",
        },
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    assert client.get(f"/api/teacher/themes/{theme['id']}").status_code == 404
    assert client.patch(
        f"/api/teacher/themes/{theme['id']}",
        json={"title": "Hack"},
    ).status_code == 404
    assert client.delete(f"/api/teacher/themes/{theme['id']}").status_code == 404
    assert (
        client.get(f"/api/teacher/themes/{theme['id']}/tasks").status_code == 404
    )
    assert client.get(f"/api/teacher/tasks/{task_id}").status_code == 404


def test_teacher_b_cannot_list_student_a_tutor_sessions(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, STUDENT_A_EMAIL)
    session = client.post("/api/tutor/sessions", json={})
    assert session.status_code == 201, session.text

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    response = client.get(f"/api/tutor/students/{client.student_a_id}/sessions")
    assert response.status_code == 403


def test_teacher_b_cannot_read_student_a_tutor_session(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, STUDENT_A_EMAIL)
    session_id = client.post("/api/tutor/sessions", json={}).json()["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    assert client.get(f"/api/tutor/sessions/{session_id}").status_code == 403


def test_teacher_b_cannot_mark_teacher_a_notification_read(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    _submit_lecture_homework(client, client.student_a_id)

    mt_logout(client)
    mt_login(client, TEACHER_A_EMAIL)
    notifications = client.get("/api/notifications")
    assert notifications.status_code == 200
    assert len(notifications.json()) >= 1
    notification_id = notifications.json()[0]["id"]

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    assert (
        client.patch(f"/api/notifications/{notification_id}/read").status_code == 403
    )


def test_teacher_b_cannot_give_feedback_on_teacher_a_homework(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_A_EMAIL)
    assignment_id = _submit_lecture_homework(client, client.student_a_id)

    mt_logout(client)
    mt_login(client, TEACHER_B_EMAIL)
    response = client.put(
        f"/api/homework/{assignment_id}/submission-feedback",
        json={"teacher_text": "Cross-tenant feedback"},
    )
    assert response.status_code == 404


def test_teacher_b_stats_exclude_teacher_a_students(
    multi_teacher_client: TestClient,
) -> None:
    client = multi_teacher_client
    mt_login(client, TEACHER_B_EMAIL)
    response = client.get("/api/teacher/students/stats")
    assert response.status_code == 200
    student_ids = {row["id"] for row in response.json()}
    assert client.student_b_id in student_ids
    assert client.student_a_id not in student_ids
