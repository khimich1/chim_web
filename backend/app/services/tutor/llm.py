"""Chat LLM factory for the chemistry tutor (provider-agnostic entry point)."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings, get_settings

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"

GIGACHAT_NOT_READY_DETAIL = (
    "GigaChat ещё не подключён. Установите LLM_PROVIDER=deepseek "
    "(или openai) и LLM_API_KEY, затем перезапустите сервер."
)

LLM_KEY_MISSING_DETAIL = (
    "LLM API key не задан. Добавьте LLM_API_KEY (или legacy OPENAI_API_KEY) "
    "в backend/.env и перезапустите сервер."
)


class LlmProviderNotConfigured(RuntimeError):
    """Raised when the selected LLM provider cannot serve chat requests yet."""


def build_chat_llm(settings: Settings | None = None) -> BaseChatModel:
    """Build the tutor chat model for the active ``LLM_PROVIDER``.

    DeepSeek / OpenAI use ``ChatOpenAI`` (OpenAI-compatible HTTP). GigaChat is
    reserved for a later increment — raises ``LlmProviderNotConfigured`` so the
    app can still start while requests return 503.
    """
    settings = settings or get_settings()
    provider = settings.llm_provider.strip().lower()

    if provider == "gigachat":
        raise LlmProviderNotConfigured(GIGACHAT_NOT_READY_DETAIL)

    if provider in ("deepseek", "openai"):
        api_key = settings.effective_llm_api_key
        base_url = settings.effective_llm_base_url or None
        return ChatOpenAI(
            model=settings.effective_llm_model,
            temperature=0,
            api_key=SecretStr(api_key) if api_key else None,
            base_url=base_url,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
