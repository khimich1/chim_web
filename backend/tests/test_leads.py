"""Tests for POST /api/leads — marketing funnel."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app

VALID_PAYLOAD = {
    "name": "Мария",
    "phone": "8 (900) 123-45-67",
    "school_class": "11",
    "goal": "ege",
    "source_page": "/zapis",
    "utm_source": "vk",
    "utm_medium": "cpc",
    "utm_campaign": "aug2026_diag",
}


@pytest.fixture
def leads_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(
        "GOOGLE_SHEETS_WEBHOOK_URL",
        "https://script.google.com/macros/s/test/exec",
    )
    get_settings.cache_clear()
    app = create_app(settings=Settings())
    with TestClient(app) as client:
        yield client


def test_create_lead_returns_201(leads_client: TestClient) -> None:
    with patch("app.services.lead_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        response = leads_client.post("/api/leads", json=VALID_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "accepted"
    assert "id" in data

    posted_json = mock_client.post.call_args.kwargs["json"]
    assert posted_json["contact"] == "+79001234567"
    assert posted_json["name"] == "Мария"
    assert posted_json["exam"] == "ЕГЭ"
    assert posted_json["source"] == "/zapis"
    assert posted_json["utm_source"] == "vk"


def test_create_lead_rejects_invalid_phone(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "phone": "123"}
    response = client.post("/api/leads", json=payload)
    assert response.status_code == 422


def test_create_lead_rejects_empty_name(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "name": ""}
    response = client.post("/api/leads", json=payload)
    assert response.status_code == 422


def test_create_lead_rate_limit(leads_client: TestClient) -> None:
    with patch("app.services.lead_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        for _ in range(5):
            response = leads_client.post("/api/leads", json=VALID_PAYLOAD)
            assert response.status_code == 201

        sixth = leads_client.post("/api/leads", json=VALID_PAYLOAD)
        assert sixth.status_code == 429


def test_create_lead_webhook_failure_still_201(
    leads_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch("app.services.lead_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=RuntimeError("webhook down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        with caplog.at_level("ERROR"):
            response = leads_client.post("/api/leads", json=VALID_PAYLOAD)

    assert response.status_code == 201
    assert any("lead_webhook_failed" in record.message for record in caplog.records)


def test_lead_create_normalizes_phone_in_schema() -> None:
    from app.schemas.leads import LeadCreate

    lead = LeadCreate(
        name="Test",
        phone="89001234567",
        school_class="10",
        goal="oge",
        source_page="/zapis",
    )
    assert lead.phone == "+79001234567"


def test_settings_google_sheets_webhook_url_optional(test_settings: Settings) -> None:
    assert test_settings.google_sheets_webhook_url is None
