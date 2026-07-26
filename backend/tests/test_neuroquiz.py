"""Neuroquiz API tests (feature flag, cache, scoring, votes)."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import ExamTrack, StudentProfile, User, UserRole

TEACHER_EMAIL = "teacher-nq@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-nq@example.com"
STUDENT_PASS = "student-pass"

TOPIC = "Соли"
CHUNK_IDX = 0


def _create_lectures_db_with_qa(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE prepared_lectures (
            topic TEXT NOT NULL,
            chunk_idx INTEGER NOT NULL,
            chunk_title TEXT,
            orig_text TEXT,
            lecture TEXT,
            tts_text TEXT,
            tts_audio BLOB,
            tts_audio_format TEXT,
            duration_ms INTEGER,
            qa_questions TEXT,
            qa_answers TEXT,
            PRIMARY KEY (topic, chunk_idx)
        )
        """
    )
    qa_q = json.dumps(
        [
            "Что такое соль?",
            "Какая формула поваренной соли?",
            "Какой тип связи в NaCl?",
            "Как получают соли?",
        ]
    )
    qa_a = json.dumps(
        [
            "Ионное соединение металла и кислотного остатка",
            "NaCl",
            "Ионная",
            "Реакцией нейтрализации",
        ]
    )
    conn.executemany(
        """
        INSERT INTO prepared_lectures
            (topic, chunk_idx, chunk_title, lecture, qa_questions, qa_answers)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (TOPIC, 0, "Введение", "# Соли\n\nСоли — ионные соединения.", qa_q, qa_a),
            (TOPIC, 1, "Свойства", "# Свойства солей\n\nСоли проводят ток.", None, None),
            ("Алканы", 0, "Алканы intro", "# Алканы", None, None),
        ],
    )
    conn.commit()
    conn.close()


def _make_client(
    tmp_path: Path,
    *,
    neuroquiz_enabled: bool,
) -> tuple[TestClient, uuid.UUID]:
    db_file = tmp_path / f"neuroquiz_{neuroquiz_enabled}.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    lectures_db = tmp_path / "prepared_lectures.db"
    if not lectures_db.exists():
        _create_lectures_db_with_qa(lectures_db)

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add_all(
                [
                    User(
                        id=teacher_id,
                        email=TEACHER_EMAIL,
                        password_hash=hash_password(TEACHER_PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email=STUDENT_EMAIL,
                        password_hash=hash_password(STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                ]
            )
            await session.flush()
            session.add(
                StudentProfile(
                    user_id=student_id,
                    teacher_id=teacher_id,
                    track=ExamTrack.EGE,
                )
            )
            await session.commit()
        await engine.dispose()

    asyncio.run(_setup())

    request_engine = create_async_engine(db_url, poolclass=NullPool)
    request_sessions = async_sessionmaker(request_engine, expire_on_commit=False)

    async def _override_get_db():
        async with request_sessions() as session:
            yield session

    get_settings.cache_clear()
    sections_yaml = Path(__file__).resolve().parent / "fixtures" / "textbook_sections_test.yaml"
    app = create_app(
        settings=Settings(
            DATABASE_URL=db_url,
            JWT_SECRET="test-jwt-secret-for-neuroquiz",
            CONTENT_LECTURES_DB_PATH=str(lectures_db),
            TEXTBOOK_SECTIONS_PATH=str(sections_yaml),
            NEUROQUIZ_ENABLED=neuroquiz_enabled,
            # Keep tests on mock generator even if developer .env has LLM keys.
            LLM_API_KEY="",
            OPENAI_API_KEY="",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    client = TestClient(app)
    client.__dict__["_request_engine"] = request_engine
    return client, student_id


def _login(client: TestClient) -> None:
    assert (
        client.post(
            "/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASS},
        ).status_code
        == 200
    )


@pytest.fixture
def client_flag_off(tmp_path: Path) -> TestClient:
    client, _ = _make_client(tmp_path, neuroquiz_enabled=False)
    with client:
        yield client
    asyncio.run(client.__dict__["_request_engine"].dispose())


@pytest.fixture
def client_flag_on(tmp_path: Path) -> TestClient:
    client, _ = _make_client(tmp_path, neuroquiz_enabled=True)
    with client:
        yield client
    asyncio.run(client.__dict__["_request_engine"].dispose())


# --- NQ-1: feature flag gate ---


def test_neuroquiz_flag_off_returns_404(client_flag_off: TestClient) -> None:
    _login(client_flag_off)
    response = client_flag_off.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert response.status_code == 404
    assert "disabled" in response.json()["detail"].lower() or "нейро" in response.json()[
        "detail"
    ].lower() or "neuroquiz" in response.json()["detail"].lower()


def test_neuroquiz_warmup_flag_off_returns_404(client_flag_off: TestClient) -> None:
    _login(client_flag_off)
    response = client_flag_off.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/warmup"
    )
    assert response.status_code == 404


def test_neuroquiz_answer_and_vote_flag_off_return_404(
    client_flag_off: TestClient,
) -> None:
    _login(client_flag_off)
    qid = str(uuid.uuid4())
    answer = client_flag_off.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": qid, "option_id": "a"},
    )
    assert answer.status_code == 404
    vote = client_flag_off.post(
        f"/api/neuroquiz/questions/{qid}/vote",
        json={"value": "like"},
    )
    assert vote.status_code == 404
    skip = client_flag_off.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/skip"
    )
    assert skip.status_code == 404


# --- NQ-2: mock generate + warmup/GET ---


def test_warmup_creates_active_questions(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    warm = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/warmup"
    )
    assert warm.status_code == 204

    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert session.status_code == 200
    body = session.json()
    assert body["topic"] == TOPIC
    assert body["chunk_idx"] == CHUNK_IDX
    assert body["scoring_enabled"] is True
    assert 1 <= len(body["questions"]) <= 4
    for q in body["questions"]:
        assert "correct_option_id" not in q
        assert len(q["options"]) == 4
        assert q["prompt"]


def test_warmup_is_idempotent(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    path = f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/warmup"
    assert client_flag_on.post(path).status_code == 204
    first = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    ids_first = [q["id"] for q in first.json()["questions"]]
    assert client_flag_on.post(path).status_code == 204
    second = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    ids_second = [q["id"] for q in second.json()["questions"]]
    assert ids_first == ids_second


async def _correct_option_map(engine, topic: str, chunk_idx: int) -> dict[str, str]:
    from sqlalchemy import select

    from app.models import NeuroQuizQuestion, NeuroQuizQuestionStatus

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        rows = (
            await session.scalars(
                select(NeuroQuizQuestion).where(
                    NeuroQuizQuestion.topic == topic,
                    NeuroQuizQuestion.chunk_idx == chunk_idx,
                    NeuroQuizQuestion.status == NeuroQuizQuestionStatus.ACTIVE,
                )
            )
        ).all()
        return {str(r.id): r.correct_option_id for r in rows}


def _get_correct_map(client: TestClient, topic: str, chunk_idx: int) -> dict[str, str]:
    engine = client.__dict__["_request_engine"]
    return asyncio.run(_correct_option_map(engine, topic, chunk_idx))


# --- NQ-3: answer + points + scoring lock ---


def test_correct_answer_awards_one_point_once(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert session.status_code == 200
    questions = session.json()["questions"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)
    q = questions[0]
    qid = q["id"]

    first = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": qid, "option_id": correct_map[qid]},
    )
    assert first.status_code == 200
    assert first.json()["correct"] is True
    assert first.json()["points_awarded"] == 1
    assert first.json()["quiz_completed"] is False

    # Same question again → 409 (already answered in pass)
    again = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": qid, "option_id": correct_map[qid]},
    )
    assert again.status_code == 409


def test_wrong_answer_shows_correct_zero_points(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    questions = session.json()["questions"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)
    q = questions[0]
    qid = q["id"]
    wrong = next(o["id"] for o in q["options"] if o["id"] != correct_map[qid])

    resp = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": qid, "option_id": wrong},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["correct"] is False
    assert body["correct_option_id"] == correct_map[qid]
    assert body["points_awarded"] == 0
    assert body["explanation"]


def test_full_pass_locks_scoring(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    questions = session.json()["questions"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)

    last_result = None
    for q in questions:
        qid = q["id"]
        last_result = client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": qid, "option_id": correct_map[qid]},
        )
        assert last_result.status_code == 200

    assert last_result is not None
    assert last_result.json()["quiz_completed"] is True

    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert again.json()["scoring_enabled"] is False

    # New open pass after completed — answers award 0
    q0 = again.json()["questions"][0]
    qid = q0["id"]
    # Need a fresh open attempt — first answer after complete creates new open attempt
    # but scoring_enabled is false because completed exists
    # Question may already be in answered list of completed attempt; create conflict
    # if same open attempt. After complete, get_open_attempt returns None → new attempt.
    ans = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": qid, "option_id": correct_map[qid]},
    )
    assert ans.status_code == 200
    assert ans.json()["points_awarded"] == 0


def test_correct_points_are_idempotent_in_student_stats(
    client_flag_on: TestClient,
) -> None:
    """Ledger + scoring lock: full correct pass awards once; replay adds 0 to stats."""
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    questions = session.json()["questions"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)

    awarded = 0
    for q in questions:
        qid = q["id"]
        resp = client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": qid, "option_id": correct_map[qid]},
        )
        assert resp.status_code == 200
        awarded += resp.json()["points_awarded"]

    assert awarded == len(questions)
    stats_after_first = client_flag_on.get("/api/students/me/stats")
    assert stats_after_first.status_code == 200
    points_after_first = stats_after_first.json()["total_points"]
    assert points_after_first >= awarded

    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert again.json()["scoring_enabled"] is False
    for q in again.json()["questions"]:
        qid = q["id"]
        resp = client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": qid, "option_id": correct_map[qid]},
        )
        assert resp.status_code == 200
        assert resp.json()["points_awarded"] == 0

    stats_after_replay = client_flag_on.get("/api/students/me/stats")
    assert stats_after_replay.status_code == 200
    assert stats_after_replay.json()["total_points"] == points_after_first


# --- NQ-4: skip + votes ---


def test_skip_does_not_lock_scoring(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    questions = session.json()["questions"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)

    # Answer one then skip
    q0 = questions[0]
    client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": q0["id"], "option_id": correct_map[q0["id"]]},
    )
    skip = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/skip"
    )
    assert skip.status_code == 204

    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert again.json()["scoring_enabled"] is True

    # Answer another unanswered question → still can get points
    q1 = questions[1]
    ans = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": q1["id"], "option_id": correct_map[q1["id"]]},
    )
    assert ans.status_code == 200
    assert ans.json()["points_awarded"] == 1


def test_skip_without_answers_keeps_scoring_enabled(
    client_flag_on: TestClient,
) -> None:
    _login(client_flag_on)
    assert (
        client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}").status_code
        == 200
    )
    skip = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/skip"
    )
    assert skip.status_code == 204
    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert again.json()["scoring_enabled"] is True


def test_dislike_retires_question_and_regenerates(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    questions = session.json()["questions"]
    assert len(questions) == 4
    qid = questions[0]["id"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)

    # Must answer before vote is accepted
    client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": qid, "option_id": correct_map[qid]},
    )
    vote = client_flag_on.post(
        f"/api/neuroquiz/questions/{qid}/vote",
        json={"value": "dislike"},
    )
    assert vote.status_code == 204

    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    ids = {q["id"] for q in again.json()["questions"]}
    assert qid not in ids
    assert len(again.json()["questions"]) == 4


def test_like_persists(client_flag_on: TestClient) -> None:
    """Like must not retire the question (still ACTIVE), even if open-pass GET omits it."""
    from app.models import NeuroQuizQuestion, NeuroQuizQuestionStatus
    from sqlalchemy import select

    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    qid = session.json()["questions"][0]["id"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": qid, "option_id": correct_map[qid]},
        ).status_code
        == 200
    )
    vote = client_flag_on.post(
        f"/api/neuroquiz/questions/{qid}/vote",
        json={"value": "like"},
    )
    assert vote.status_code == 204

    # Open attempt filters answered IDs out of GET — that is expected.
    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert again.status_code == 200
    assert qid not in {q["id"] for q in again.json()["questions"]}

    engine = client_flag_on.__dict__["_request_engine"]

    async def _status() -> NeuroQuizQuestionStatus:
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as db:
            row = await db.scalar(
                select(NeuroQuizQuestion).where(NeuroQuizQuestion.id == uuid.UUID(qid))
            )
            assert row is not None
            return row.status

    assert asyncio.run(_status()) == NeuroQuizQuestionStatus.ACTIVE


def test_like_then_dislike_retires_question(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    qid = session.json()["questions"][0]["id"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": qid, "option_id": correct_map[qid]},
        ).status_code
        == 200
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/questions/{qid}/vote",
            json={"value": "like"},
        ).status_code
        == 204
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/questions/{qid}/vote",
            json={"value": "dislike"},
        ).status_code
        == 204
    )
    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert qid not in {q["id"] for q in again.json()["questions"]}
    assert len(again.json()["questions"]) == 4


# --- Security: scoring-lock bypass + vote without answer ---


def test_answer_dislike_loop_cannot_exceed_four_points_per_chunk(
    client_flag_on: TestClient,
) -> None:
    """Farming replacements via dislike must not exceed +4 points or leave lock open."""
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert session.status_code == 200
    questions = session.json()["questions"]
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)
    total_awarded = 0

    # Seed: answer one original question, then farm only replacements.
    qid = questions[0]["id"]
    ids_before = {q["id"] for q in questions}
    ans = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": qid, "option_id": correct_map[qid]},
    )
    assert ans.status_code == 200
    total_awarded += ans.json()["points_awarded"]
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/questions/{qid}/vote",
            json={"value": "dislike"},
        ).status_code
        == 204
    )

    for _ in range(5):
        after = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
        assert after.status_code == 200
        ids_after = {q["id"] for q in after.json()["questions"]}
        new_ids = ids_after - ids_before
        assert new_ids, "dislike should introduce a replacement question"
        qid = next(iter(new_ids))
        correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)

        ans = client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": qid, "option_id": correct_map[qid]},
        )
        assert ans.status_code == 200
        total_awarded += ans.json()["points_awarded"]

        ids_before = ids_after
        vote = client_flag_on.post(
            f"/api/neuroquiz/questions/{qid}/vote",
            json={"value": "dislike"},
        )
        assert vote.status_code == 204

    assert total_awarded <= 4

    locked = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert locked.status_code == 200
    assert locked.json()["scoring_enabled"] is False


def test_vote_without_answer_rejected(client_flag_on: TestClient) -> None:
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert session.status_code == 200
    qid = session.json()["questions"][0]["id"]

    like = client_flag_on.post(
        f"/api/neuroquiz/questions/{qid}/vote",
        json={"value": "like"},
    )
    assert like.status_code in (400, 403)

    dislike = client_flag_on.post(
        f"/api/neuroquiz/questions/{qid}/vote",
        json={"value": "dislike"},
    )
    assert dislike.status_code in (400, 403)


def test_skip_mid_pass_reopen_omits_answered_and_next_answer_succeeds(
    client_flag_on: TestClient,
) -> None:
    """Skip/Escape leaves open attempt; GET must omit answered so index-0 is answerable."""
    _login(client_flag_on)
    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert session.status_code == 200
    questions = session.json()["questions"]
    assert len(questions) >= 2
    correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)

    q0 = questions[0]
    q1 = questions[1]
    first = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": q0["id"], "option_id": correct_map[q0["id"]]},
    )
    assert first.status_code == 200
    assert first.json()["quiz_completed"] is False

    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/skip"
        ).status_code
        == 204
    )

    again = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert again.status_code == 200
    body = again.json()
    assert body["scoring_enabled"] is True
    reopen_ids = [q["id"] for q in body["questions"]]
    assert q0["id"] not in reopen_ids
    assert q1["id"] in reopen_ids
    assert reopen_ids[0] == q1["id"]

    # Re-answering Q0 must still 409; answering first remaining succeeds
    conflict = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": q0["id"], "option_id": correct_map[q0["id"]]},
    )
    assert conflict.status_code == 409

    nxt = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
        json={"question_id": reopen_ids[0], "option_id": correct_map[reopen_ids[0]]},
    )
    assert nxt.status_code == 200
    assert nxt.json()["quiz_completed"] is False


def test_neuroquiz_unauthenticated_returns_401(client_flag_on: TestClient) -> None:
    assert (
        client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}").status_code
        == 401
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/warmup"
        ).status_code
        == 401
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": str(uuid.uuid4()), "option_id": "a"},
        ).status_code
        == 401
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/skip"
        ).status_code
        == 401
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/questions/{uuid.uuid4()}/vote",
            json={"value": "like"},
        ).status_code
        == 401
    )


def test_neuroquiz_teacher_returns_403(client_flag_on: TestClient) -> None:
    assert (
        client_flag_on.post(
            "/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASS},
        ).status_code
        == 200
    )
    assert (
        client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}").status_code
        == 403
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/warmup"
        ).status_code
        == 403
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/answer",
            json={"question_id": str(uuid.uuid4()), "option_id": "a"},
        ).status_code
        == 403
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/skip"
        ).status_code
        == 403
    )
    assert (
        client_flag_on.post(
            f"/api/neuroquiz/questions/{uuid.uuid4()}/vote",
            json={"value": "like"},
        ).status_code
        == 403
    )


# --- NQ-7: LLM generator with fake adapter ---


def test_build_neuroquiz_generator_uses_llm_api_key_not_only_openai() -> None:
    """DeepSeek / LLM_API_KEY must enable real generator (not openai_api_key-only)."""
    from app.services.neuroquiz_generate import (
        LlmNeuroQuizGenerator,
        MockNeuroQuizGenerator,
        build_neuroquiz_generator,
    )

    llm_only = Settings(
        LLM_API_KEY="sk-deepseek-test",
        LLM_PROVIDER="deepseek",
        LLM_MODEL="deepseek-chat",
        OPENAI_API_KEY="",
    )
    gen = build_neuroquiz_generator(llm_only)
    assert isinstance(gen, LlmNeuroQuizGenerator)

    neither = Settings(LLM_API_KEY="", OPENAI_API_KEY="")
    assert isinstance(build_neuroquiz_generator(neither), MockNeuroQuizGenerator)


def test_llm_generator_wires_effective_llm_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import neuroquiz_generate as nq_gen

    captured: dict = {}

    class _FakeChatOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def invoke(self, _prompt: str) -> object:
            class _Resp:
                content = "[]"

            return _Resp()

    monkeypatch.setattr(
        "langchain_openai.ChatOpenAI",
        _FakeChatOpenAI,
    )
    # Also patch the local import path used inside _get_llm
    import langchain_openai

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", _FakeChatOpenAI)

    settings = Settings(
        LLM_API_KEY="sk-deepseek-test",
        LLM_PROVIDER="deepseek",
        LLM_MODEL="deepseek-chat",
        LLM_BASE_URL="",
        OPENAI_API_KEY="",
    )
    gen = nq_gen.LlmNeuroQuizGenerator(settings)
    llm = gen._get_llm()
    assert llm is not None
    assert captured.get("base_url") == "https://api.deepseek.com"
    assert captured.get("model") == "deepseek-chat"


def test_llm_generator_uses_valid_json_and_rejects_garbage() -> None:
    from app.models.enums import NeuroQuizQuestionSource
    from app.repositories.content.lectures import SelfCheckQA
    from app.services.neuroquiz_generate import (
        LlmNeuroQuizGenerator,
        MockNeuroQuizGenerator,
        validate_mcq_payload,
    )

    assert (
        validate_mcq_payload(
            {
                "prompt": "Q?",
                "options": [
                    {"id": "a", "text": "1"},
                    {"id": "b", "text": "2"},
                    {"id": "c", "text": "3"},
                ],
                "correct_option_id": "a",
            },
            source=NeuroQuizQuestionSource.LECTURE_GEN,
        )
        is None
    )

    class _FakeLLM:
        def invoke(self, _prompt: str):
            class _Resp:
                content = json.dumps(
                    [
                        {
                            "prompt": "Что такое соль?",
                            "options": [
                                {"id": "a", "text": "Ионное соединение"},
                                {"id": "b", "text": "Металл"},
                                {"id": "c", "text": "Газ"},
                                {"id": "d", "text": "Кислота"},
                            ],
                            "correct_option_id": "a",
                            "explanation": "Определение",
                            "source": "qa_pair",
                        }
                    ]
                )

            return _Resp()

    gen = LlmNeuroQuizGenerator(
        llm=_FakeLLM(),
        fallback=MockNeuroQuizGenerator(),
    )
    items = gen.generate_for_chunk(
        topic=TOPIC,
        chunk_idx=0,
        lecture="# Соли",
        qa_pairs=[
            SelfCheckQA(
                question="Что такое соль?",
                answer="Ионное соединение",
                chunk_idx=0,
                chunk_title="Введение",
            )
        ],
        need=1,
    )
    assert len(items) == 1
    assert items[0].correct_option_id == "a"
    assert len(items[0].options) == 4


def test_llm_generator_falls_back_on_invalid_json() -> None:
    from app.services.neuroquiz_generate import LlmNeuroQuizGenerator, MockNeuroQuizGenerator

    class _BadLLM:
        def invoke(self, _prompt: str):
            class _Resp:
                content = "not-json{{{"

            return _Resp()

    gen = LlmNeuroQuizGenerator(llm=_BadLLM(), fallback=MockNeuroQuizGenerator())
    items = gen.generate_for_chunk(
        topic=TOPIC,
        chunk_idx=0,
        lecture="# Соли ионные соединения металла с кислотным остатком.",
        qa_pairs=[],
        need=2,
    )
    assert len(items) == 2


def test_mock_distractors_are_not_generic_filler() -> None:
    from app.repositories.content.lectures import SelfCheckQA
    from app.services.neuroquiz_generate import (
        GENERIC_DISTRACTOR_DENYLIST,
        MockNeuroQuizGenerator,
        options_have_generic_junk,
    )

    gen = MockNeuroQuizGenerator()
    items = gen.generate_for_chunk(
        topic="Кислоты",
        chunk_idx=0,
        lecture="Кислота — сложное вещество, содержащее атомы водорода.",
        qa_pairs=[
            SelfCheckQA(
                question="Что такое кислота?",
                answer="Сложное вещество, содержащее атомы водорода",
                chunk_idx=0,
                chunk_title="Кислоты",
            ),
            SelfCheckQA(
                question="Пример кислоты?",
                answer="H2SO4",
                chunk_idx=0,
                chunk_title="Кислоты",
            ),
            SelfCheckQA(
                question="Чему равна валентность кислорода?",
                answer="II",
                chunk_idx=0,
                chunk_title="Кислоты",
            ),
        ],
        need=1,
    )
    assert len(items) == 1
    texts = [opt["text"] for opt in items[0].options]
    assert not options_have_generic_junk([{"text": t} for t in texts])
    for phrase in GENERIC_DISTRACTOR_DENYLIST:
        assert phrase not in texts


def test_mock_distractors_must_not_reuse_sibling_qa_answers() -> None:
    """Bug: other true QA answers from the same chunk used as 'wrong' options."""
    from app.repositories.content.lectures import SelfCheckQA
    from app.services.neuroquiz_generate import MockNeuroQuizGenerator

    qa_pairs = [
        SelfCheckQA(
            question="Что такое кислота?",
            answer="Сложное вещество, содержащее атомы водорода",
            chunk_idx=0,
            chunk_title="Кислоты",
        ),
        SelfCheckQA(
            question="Признак кислоты?",
            answer="Наличие ионов водорода",
            chunk_idx=0,
            chunk_title="Кислоты",
        ),
        SelfCheckQA(
            question="Что образуется при нейтрализации?",
            answer="Соль и вода",
            chunk_idx=0,
            chunk_title="Кислоты",
        ),
        SelfCheckQA(
            question="Пример кислоты?",
            answer="H2SO4",
            chunk_idx=0,
            chunk_title="Кислоты",
        ),
    ]
    sibling_facts = {
        "Наличие ионов водорода",
        "Соль и вода",
        "H2SO4",
    }
    gen = MockNeuroQuizGenerator()
    items = gen.generate_for_chunk(
        topic="Кислоты",
        chunk_idx=0,
        lecture=(
            "Кислота — сложное вещество с атомами водорода. "
            "Признак — ионы водорода. Нейтрализация даёт соль и воду. Пример — H2SO4."
        ),
        qa_pairs=qa_pairs,
        need=1,
    )
    assert len(items) == 1
    correct = next(
        o["text"] for o in items[0].options if o["id"] == items[0].correct_option_id
    )
    assert correct == "Сложное вещество, содержащее атомы водорода"
    distractors = [
        o["text"] for o in items[0].options if o["id"] != items[0].correct_option_id
    ]
    assert len(distractors) == 3
    for d in distractors:
        assert d not in sibling_facts, f"sibling-true distractor leaked: {d!r}"


def test_validate_mcq_rejects_generic_distractors() -> None:
    from app.models.enums import NeuroQuizQuestionSource
    from app.services.neuroquiz_generate import validate_mcq_payload

    assert (
        validate_mcq_payload(
            {
                "prompt": "Что такое кислота?",
                "options": [
                    {"id": "a", "text": "Сложное вещество с водородом"},
                    {"id": "b", "text": "Это не относится к данной теме"},
                    {"id": "c", "text": "Основание"},
                    {"id": "d", "text": "Соль"},
                ],
                "correct_option_id": "a",
            },
            source=NeuroQuizQuestionSource.LECTURE_GEN,
        )
        is None
    )


def test_validate_mcq_rejects_sibling_true_distractors() -> None:
    """LLM payloads that reuse other lecture true facts as wrong options are invalid."""
    from app.models.enums import NeuroQuizQuestionSource
    from app.services.neuroquiz_generate import validate_mcq_payload

    true_facts = [
        "Сложное вещество, содержащее атомы водорода",
        "Наличие ионов водорода",
        "Соль и вода",
    ]
    assert (
        validate_mcq_payload(
            {
                "prompt": "Что такое кислота?",
                "options": [
                    {"id": "a", "text": "Сложное вещество, содержащее атомы водорода"},
                    {"id": "b", "text": "Наличие ионов водорода"},
                    {"id": "c", "text": "Соль и вода"},
                    {"id": "d", "text": "Основание без водорода"},
                ],
                "correct_option_id": "a",
                "explanation": "a верно; b и c — другие факты главы, не определение",
            },
            source=NeuroQuizQuestionSource.QA_PAIR,
            true_facts=true_facts,
        )
        is None
    )

    ok = validate_mcq_payload(
        {
            "prompt": "Что такое кислота?",
            "options": [
                {"id": "a", "text": "Сложное вещество, содержащее атомы водорода"},
                {"id": "b", "text": "Простое вещество — металл"},
                {"id": "c", "text": "Основание (гидроксид)"},
                {"id": "d", "text": "Сложное вещество без атомов водорода"},
            ],
            "correct_option_id": "a",
            "explanation": "Определение из текста",
        },
        source=NeuroQuizQuestionSource.QA_PAIR,
        true_facts=true_facts,
    )
    assert ok is not None
    assert ok.correct_option_id == "a"


def test_warmup_retires_questions_with_generic_distractors(
    client_flag_on: TestClient,
) -> None:
    """Cached mock junk is retired on ensure/warmup so students see fresh options."""
    from app.models import NeuroQuizQuestion, NeuroQuizQuestionStatus
    from app.models.enums import NeuroQuizQuestionSource

    _login(client_flag_on)
    engine = client_flag_on.__dict__["_request_engine"]

    async def _seed_junk() -> str:
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            row = NeuroQuizQuestion(
                topic=TOPIC,
                chunk_idx=CHUNK_IDX,
                position=0,
                prompt="Что такое кислота?",
                options_json=[
                    {"id": "a", "text": "Сложное вещество с H"},
                    {"id": "b", "text": "Это не относится к данной теме"},
                    {"id": "c", "text": "Верно только при особых условиях"},
                    {"id": "d", "text": "Смесь простых веществ"},
                ],
                correct_option_id="a",
                explanation="Тест",
                source=NeuroQuizQuestionSource.QA_PAIR,
                status=NeuroQuizQuestionStatus.ACTIVE,
            )
            session.add(row)
            await session.commit()
            return str(row.id)

    junk_id = asyncio.run(_seed_junk())

    warm = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/warmup"
    )
    assert warm.status_code == 204

    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert session.status_code == 200
    ids = {q["id"] for q in session.json()["questions"]}
    assert junk_id not in ids
    for q in session.json()["questions"]:
        texts = [opt["text"] for opt in q["options"]]
        assert "Это не относится к данной теме" not in texts
        assert "Верно только при особых условиях" not in texts


def test_warmup_retires_sibling_true_and_outdated_generation(
    client_flag_on: TestClient,
) -> None:
    """Cached MCQs with sibling QA answers as distractors (or old gen) are retired."""
    from app.models import NeuroQuizQuestion, NeuroQuizQuestionStatus
    from app.models.enums import NeuroQuizQuestionSource
    from app.services.neuroquiz_generate import GENERATION_VERSION, generation_marker

    _login(client_flag_on)
    engine = client_flag_on.__dict__["_request_engine"]

    async def _seed_bad() -> tuple[str, str]:
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            sibling = NeuroQuizQuestion(
                topic=TOPIC,
                chunk_idx=CHUNK_IDX,
                position=0,
                prompt="Что такое соль?",
                options_json=[
                    {"id": "a", "text": "Ионное соединение металла и кислотного остатка"},
                    {"id": "b", "text": "NaCl"},
                    {"id": "c", "text": "Ионная"},
                    {"id": "d", "text": "Реакцией нейтрализации"},
                ],
                correct_option_id="a",
                explanation=f"Старый кэш {generation_marker(1)}",
                source=NeuroQuizQuestionSource.QA_PAIR,
                status=NeuroQuizQuestionStatus.ACTIVE,
            )
            outdated = NeuroQuizQuestion(
                topic=TOPIC,
                chunk_idx=CHUNK_IDX,
                position=1,
                prompt="Какая формула поваренной соли?",
                options_json=[
                    {"id": "a", "text": "NaCl"},
                    {"id": "b", "text": "KCl"},
                    {"id": "c", "text": "Na2O"},
                    {"id": "d", "text": "HCl"},
                ],
                correct_option_id="a",
                explanation="Без маркера версии",
                source=NeuroQuizQuestionSource.QA_PAIR,
                status=NeuroQuizQuestionStatus.ACTIVE,
            )
            session.add_all([sibling, outdated])
            await session.commit()
            return str(sibling.id), str(outdated.id)

    sibling_id, outdated_id = asyncio.run(_seed_bad())
    assert GENERATION_VERSION >= 2

    warm = client_flag_on.post(
        f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}/warmup"
    )
    assert warm.status_code == 204

    session = client_flag_on.get(f"/api/neuroquiz/topics/{TOPIC}/chunks/{CHUNK_IDX}")
    assert session.status_code == 200
    ids = {q["id"] for q in session.json()["questions"]}
    assert sibling_id not in ids
    assert outdated_id not in ids
    # Fresh questions must not reuse other qa answers from the chunk as distractors
    sibling_answers = {"NaCl", "Ионная", "Реакцией нейтрализации"}
    for q in session.json()["questions"]:
        if q["prompt"] != "Что такое соль?":
            continue
        correct_map = _get_correct_map(client_flag_on, TOPIC, CHUNK_IDX)
        cid = correct_map[q["id"]]
        for opt in q["options"]:
            if opt["id"] == cid:
                continue
            assert opt["text"] not in sibling_answers
