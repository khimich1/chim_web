"""Textbook sections API and YAML validation tests (Phase 18)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import ExamTrack, StudentProfile, User, UserRole
from app.schemas.textbook_sections import TopicConfigEntry, validate_video_url
from app.services.textbook_sections_config import TextbookSectionsConfigError
from tests.content.conftest import _create_lectures_db
from tests.test_textbook import STUDENT_EMAIL, STUDENT_PASS, _login

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "sections_app.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    lectures_db = tmp_path / "prepared_lectures.db"
    _create_lectures_db(lectures_db)

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
                        email="teacher@example.com",
                        password_hash=hash_password("teacher-pass"),
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
    app = create_app(
        settings=Settings(
            DATABASE_URL=db_url,
            JWT_SECRET="test-jwt-secret-for-sections",
            CONTENT_LECTURES_DB_PATH=str(lectures_db),
            TEXTBOOK_SECTIONS_PATH=str(FIXTURES_DIR / "textbook_sections_test.yaml"),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def test_list_sections_returns_three_parts(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.get("/api/textbook/sections")
    assert response.status_code == 200
    body = response.json()
    assert [item["section_id"] for item in body] == ["basics", "elements", "organic"]
    assert body[0]["title"] == "Начала химии"
    assert body[0]["topic_count"] == 1
    assert body[1]["topic_count"] == 0
    assert body[2]["topic_count"] == 1


def test_list_topics_filtered_by_section(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    basics = client.get("/api/textbook/topics", params={"section": "basics"})
    assert basics.status_code == 200
    assert [item["topic"] for item in basics.json()] == ["Соли"]
    assert basics.json()[0]["section"] == "basics"

    organic = client.get("/api/textbook/topics", params={"section": "organic"})
    assert organic.status_code == 200
    assert [item["topic"] for item in organic.json()] == ["Алканы"]


def test_unknown_section_returns_422(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.get("/api/textbook/topics", params={"section": "unknown"})
    assert response.status_code == 422


def test_validate_video_url_rejects_untrusted_host() -> None:
    with pytest.raises(ValidationError):
        TopicConfigEntry(
            topic="Соли",
            video_url="https://evil.example.com/video",
        )


def test_validate_video_url_accepts_youtube() -> None:
    entry = TopicConfigEntry(
        topic="Соли",
        video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )
    assert validate_video_url(entry.video_url) == entry.video_url


def test_production_yaml_matches_db_topics() -> None:
    from app.repositories.content.lectures import LectureContentRepo
    from app.services.textbook_sections_config import get_textbook_sections_config

    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "prepared_lectures.db"
    yaml_path = repo_root / "backend" / "app" / "data" / "textbook_sections.yaml"

    if not db_path.is_file():
        pytest.skip("prepared_lectures.db not available in CI")

    repo = LectureContentRepo(db_path)
    db_topics = {topic.topic for topic in repo.list_topics()}
    config = get_textbook_sections_config(yaml_path, db_topics)
    assert len(config.list_sections()) == 3
    assert sum(count for _, _, count in config.list_sections()) == len(db_topics)


def test_yaml_with_unknown_topic_raises(tmp_path: Path) -> None:
    from app.repositories.content.lectures import LectureContentRepo
    from app.services.textbook_sections_config import get_textbook_sections_config

    lectures_db = tmp_path / "prepared_lectures.db"
    _create_lectures_db(lectures_db)
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        """
sections:
  basics:
    title: "Начала химии"
    topics:
      - topic: "Нет такой"
  elements:
    title: "Химия элементов"
    topics: []
  organic:
    title: "Органическая химия"
    topics:
      - topic: "Алканы"
""".strip(),
        encoding="utf-8",
    )

    repo = LectureContentRepo(lectures_db)
    db_topics = {topic.topic for topic in repo.list_topics()}

    with pytest.raises(TextbookSectionsConfigError, match="missing from DB"):
        get_textbook_sections_config(bad_yaml, db_topics)
