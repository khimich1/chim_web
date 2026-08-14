"""Application settings via pydantic-settings.

Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import BeforeValidator, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_cors_origins(value: object) -> list[str]:
    if isinstance(value, str):
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    if isinstance(value, list):
        return [str(origin) for origin in value]
    raise ValueError("CORS_ORIGINS must be a comma-separated string or list")

# Monorepo root: backend/app/core/config.py -> parents[3]
_MONOREPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    auth_login_rate_limit: str = Field(
        default="10/15minutes",
        alias="AUTH_LOGIN_RATE_LIMIT",
    )
    tutor_message_rate_limit: str = Field(
        default="30/minute",
        alias="TUTOR_MESSAGE_RATE_LIMIT",
    )
    leads_rate_limit: str = Field(
        default="5/minute",
        alias="LEADS_RATE_LIMIT",
    )

    google_sheets_webhook_url: str | None = Field(
        default=None,
        alias="GOOGLE_SHEETS_WEBHOOK_URL",
    )

    # Auth cookie settings. In dev (http://localhost) Secure must be False;
    # set COOKIE_SECURE=true behind HTTPS in production.
    cookie_name: str = Field(default="access_token", alias="COOKIE_NAME")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_samesite: str = Field(default="lax", alias="COOKIE_SAMESITE")

    cors_origins: Annotated[
        list[str],
        NoDecode,
        BeforeValidator(_parse_cors_origins),
    ] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    frontend_url: str = Field(
        default="http://localhost:3000",
        alias="FRONTEND_URL",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    content_ege_db_path: Path = Field(
        default=_MONOREPO_ROOT / "test_ege.db",
        alias="CONTENT_EGE_DB_PATH",
    )
    content_oge_db_path: Path = Field(
        default=_MONOREPO_ROOT / "test_oge.db",
        alias="CONTENT_OGE_DB_PATH",
    )
    content_lectures_db_path: Path = Field(
        default=_MONOREPO_ROOT / "prepared_lectures.db",
        alias="CONTENT_LECTURES_DB_PATH",
    )
    textbook_sections_path: Path = Field(
        default=_MONOREPO_ROOT / "backend" / "app" / "data" / "textbook_sections.yaml",
        alias="TEXTBOOK_SECTIONS_PATH",
    )

    rag_index_path: Path = Field(
        default=_MONOREPO_ROOT / "backend" / "data" / "rag_index.json",
        alias="RAG_INDEX_PATH",
    )

    # Tutor chat LLM (v2+). Canonical: LLM_*; OPENAI_* remain legacy aliases.
    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    # Legacy aliases + embeddings / hybrid RAG (unchanged readers of openai_*)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    rag_top_k: int = Field(default=5, ge=1, le=20, alias="RAG_TOP_K")
    rag_hybrid_enabled: bool = Field(default=True, alias="RAG_HYBRID_ENABLED")
    rag_query_rewrite_enabled: bool = Field(
        default=True,
        alias="RAG_QUERY_REWRITE_ENABLED",
    )
    neuroquiz_enabled: bool = Field(default=False, alias="NEUROQUIZ_ENABLED")
    # Max seconds to wait for a single tutor agent (LangGraph) invocation before
    # returning 504. Guards the worker thread pool against a hung LLM call.
    tutor_invoke_timeout: float = Field(
        default=60.0,
        gt=0,
        alias="TUTOR_INVOKE_TIMEOUT",
    )
    chroma_dir: Path = Field(
        default=_MONOREPO_ROOT / "backend" / "data" / "chroma",
        alias="CHROMA_DIR",
    )
    chroma_lectures_collection: str = Field(
        default="lectures",
        alias="CHROMA_LECTURES_COLLECTION",
    )
    tutor_profile_dir: Path = Field(
        default=_MONOREPO_ROOT / "backend" / "data" / "tutor_profiles",
        alias="TUTOR_PROFILE_DIR",
    )

    upload_dir: Path = Field(
        default=_MONOREPO_ROOT / "backend" / "uploads",
        alias="UPLOAD_DIR",
    )
    upload_max_bytes: int = Field(
        default=5 * 1024 * 1024,
        alias="UPLOAD_MAX_BYTES",
    )
    upload_allowed_mime: list[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        alias="UPLOAD_ALLOWED_MIME",
    )
    upload_audio_max_bytes: int = Field(
        default=15 * 1024 * 1024,
        alias="UPLOAD_AUDIO_MAX_BYTES",
    )
    upload_audio_max_duration_sec: int = Field(
        default=600,
        alias="UPLOAD_AUDIO_MAX_DURATION_SEC",
    )
    upload_audio_allowed_mime: list[str] = Field(
        default=["audio/webm", "audio/ogg"],
        alias="UPLOAD_AUDIO_ALLOWED_MIME",
    )

    @property
    def effective_llm_api_key(self) -> str:
        """Chat LLM key: LLM_API_KEY wins; else OPENAI_API_KEY alias."""
        return self.llm_api_key.strip() or self.openai_api_key.strip()

    @property
    def effective_llm_model(self) -> str:
        """Chat model: LLM_MODEL when LLM key set; else OPENAI_MODEL on openai-key fallback."""
        if self.llm_api_key.strip():
            return self.llm_model
        if self.openai_api_key.strip():
            return self.openai_model
        return self.llm_model

    @property
    def effective_llm_base_url(self) -> str:
        """Explicit LLM_BASE_URL, else DeepSeek default host when provider=deepseek."""
        if self.llm_base_url.strip():
            return self.llm_base_url.strip()
        if self.llm_provider.strip().lower() == "deepseek":
            return "https://api.deepseek.com"
        return ""

    @property
    def llm_configured(self) -> bool:
        """True when an effective chat API key is present for the active provider path."""
        return bool(self.effective_llm_api_key)

    def tests_db_path_for_track(self, track: str) -> Path:
        if track == "oge":
            return self.content_oge_db_path
        return self.content_ege_db_path

    @field_validator(
        "content_ege_db_path",
        "content_oge_db_path",
        "content_lectures_db_path",
        mode="before",
    )
    @classmethod
    def resolve_content_path(cls, value: str | Path) -> Path:
        path = value if isinstance(value, Path) else Path(value)
        if not path.is_absolute():
            path = (_MONOREPO_ROOT / "backend" / path).resolve()
        return path.resolve()

    @field_validator("rag_index_path", mode="before")
    @classmethod
    def resolve_rag_index_path(cls, value: str | Path) -> Path:
        path = value if isinstance(value, Path) else Path(value)
        if not path.is_absolute():
            return (_MONOREPO_ROOT / path).resolve()
        return path.resolve()

    @field_validator(
        "chroma_dir",
        "tutor_profile_dir",
        "upload_dir",
        mode="before",
    )
    @classmethod
    def resolve_data_path(cls, value: str | Path) -> Path:
        path = value if isinstance(value, Path) else Path(value)
        if not path.is_absolute():
            return (_MONOREPO_ROOT / path).resolve()
        return path.resolve()

    def content_db_paths(self) -> dict[str, Path]:
        return {
            "ege": self.content_ege_db_path,
            "oge": self.content_oge_db_path,
            "lectures": self.content_lectures_db_path,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
