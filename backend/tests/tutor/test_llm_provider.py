"""Unit tests for LLM provider settings + build_chat_llm factory."""

from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from app.core.config import Settings
from app.services.tutor.llm import (
    DEFAULT_DEEPSEEK_BASE_URL,
    GIGACHAT_NOT_READY_DETAIL,
    LlmProviderNotConfigured,
    build_chat_llm,
)


def test_effective_llm_api_key_prefers_llm_over_openai() -> None:
    settings = Settings(
        llm_api_key="llm-key",
        openai_api_key="openai-key",
    )
    assert settings.effective_llm_api_key == "llm-key"
    assert settings.llm_configured is True


def test_effective_llm_api_key_falls_back_to_openai() -> None:
    settings = Settings(llm_api_key="", openai_api_key="openai-key")
    assert settings.effective_llm_api_key == "openai-key"
    assert settings.llm_configured is True


def test_effective_llm_model_uses_openai_model_on_openai_key_fallback() -> None:
    settings = Settings(
        llm_api_key="",
        llm_model="deepseek-chat",
        openai_api_key="openai-key",
        openai_model="gpt-4o-mini",
    )
    assert settings.effective_llm_model == "gpt-4o-mini"


def test_effective_llm_model_uses_llm_model_when_llm_key_set() -> None:
    settings = Settings(
        llm_api_key="llm-key",
        llm_model="deepseek-chat",
        openai_api_key="openai-key",
        openai_model="gpt-4o-mini",
    )
    assert settings.effective_llm_model == "deepseek-chat"


def test_llm_configured_false_without_any_key() -> None:
    settings = Settings(llm_api_key="", openai_api_key="")
    assert settings.llm_configured is False
    assert settings.effective_llm_api_key == ""


def test_effective_llm_base_url_defaults_for_deepseek() -> None:
    settings = Settings(llm_provider="deepseek", llm_base_url="")
    assert settings.effective_llm_base_url == DEFAULT_DEEPSEEK_BASE_URL


def test_effective_llm_base_url_empty_for_openai_without_override() -> None:
    settings = Settings(llm_provider="openai", llm_base_url="")
    assert settings.effective_llm_base_url == ""


def test_build_chat_llm_deepseek_uses_base_url_and_model() -> None:
    settings = Settings(
        llm_provider="deepseek",
        llm_api_key="sk-deepseek",
        llm_model="deepseek-chat",
        llm_base_url="",
    )
    llm = build_chat_llm(settings)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "deepseek-chat"
    assert llm.openai_api_base == DEFAULT_DEEPSEEK_BASE_URL


def test_build_chat_llm_openai_provider_without_custom_base() -> None:
    settings = Settings(
        llm_provider="openai",
        llm_api_key="sk-openai",
        llm_model="gpt-4o-mini",
        llm_base_url="",
    )
    llm = build_chat_llm(settings)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"


def test_build_chat_llm_gigachat_raises_not_configured() -> None:
    settings = Settings(
        llm_provider="gigachat",
        llm_api_key="gigachat-creds",
    )
    with pytest.raises(LlmProviderNotConfigured, match="GigaChat") as exc_info:
        build_chat_llm(settings)
    assert str(exc_info.value) == GIGACHAT_NOT_READY_DETAIL


def test_build_chat_llm_unknown_provider_raises_value_error() -> None:
    settings = Settings(llm_provider="ollama", llm_api_key="x")
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        build_chat_llm(settings)
