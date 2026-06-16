# Testing Patterns — Backend (FastAPI / pytest)

Справочник для `test-driven-development`. Стек: **pytest**, **httpx/TestClient**, **FastAPI**.

Frontend (Vitest, Playwright, MSW): см. [testing-patterns-frontend.md](testing-patterns-frontend.md).

## Arrange-Act-Assert

```python
def test_create_task_returns_pending_status(client, auth_headers):
    # Arrange
    payload = {"title": "Test Task", "priority": "high"}

    # Act
    response = client.post("/api/tasks", json=payload, headers=auth_headers)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"
    assert data["status"] == "pending"
```

## Именование

```python
class TestTaskServiceCreate:
    def test_creates_task_with_default_pending_status(self): ...
    def test_raises_validation_error_when_title_empty(self): ...
    def test_trims_whitespace_from_title(self): ...
```

Паттерн: `[unit] [ожидаемое поведение] [условие]`

## pytest assertions

```python
assert result == expected
assert result is not None
assert "key" in result
assert len(items) == 3

with pytest.raises(ValidationError):
    TaskCreate(title="")

with pytest.raises(HTTPException) as exc:
    await service.get_task("missing")
assert exc.value.status_code == 404

# async
result = await service.create(data)
assert result.title == "Test"
```

## Фикстуры (conftest.py)

```python
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_session

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def override_db(session):
    app.dependency_overrides[get_session] = lambda: session
    yield
    app.dependency_overrides.clear()
```

## Mock на границах

```
Mock:                    Не mock:
├── Внешние HTTP API     ├── Service logic
├── Email sending        ├── Pydantic validation
├── S3 / file storage    ├── Pure functions
└── Test DB (или fake)   └── Repository (prefer real test DB)
```

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_send_notification_calls_email_service():
    with patch("app.services.notification.send_email", new_callable=AsyncMock) as mock:
        await service.notify_user(user_id=1, message="Hi")
        mock.assert_called_once()
```

## API Integration Tests

```python
def test_post_tasks_creates_and_returns_201(client, auth_headers):
    response = client.post(
        "/api/tasks",
        json={"title": "Test Task"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Task"

def test_post_tasks_returns_422_for_empty_title(client, auth_headers):
    response = client.post(
        "/api/tasks",
        json={"title": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422

def test_post_tasks_returns_401_without_auth(client):
    response = client.post("/api/tasks", json={"title": "Test"})
    assert response.status_code == 401
```

## Service Unit Tests

```python
@pytest.mark.asyncio
async def test_complete_task_sets_timestamp(task_service, mock_repo):
    task = Task(id=uuid4(), title="T", status="pending")
    mock_repo.get_by_id.return_value = task
    mock_repo.update.return_value = task

    result = await task_service.complete(task.id)

    mock_repo.update.assert_called_once()
    assert result.status == "completed"
```

## Test DB

```python
# tests/conftest.py — типичный паттерн
@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
        await session.rollback()
```

## Команды

```bash
pytest                          # все тесты
pytest backend/tests/test_tasks.py -v   # один файл
pytest -k "create_task"         # по имени
pytest --cov=app --cov-report=term-missing
pytest -x                       # стоп на первом fail
```

## Anti-Patterns

| Anti-Pattern | Проблема | Лучше |
|---|---|---|
| Тест implementation details | Ломается при refactor | Input/output |
| Shared mutable state | Flaky tests | Fixture per test + rollback |
| Mock всего подряд | Pass в CI, fail в prod | Real test DB |
| `@pytest.mark.skip` навсегда | Мёртвый код | Fix or delete |
| Нет `await` в async test | False positive | `@pytest.mark.asyncio` |
| Один гигантский test | Непонятно что сломалось | Один concept на test |
