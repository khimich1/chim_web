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
    )

    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    cors_origins: Annotated[
        list[str],
        NoDecode,
        BeforeValidator(_parse_cors_origins),
    ] = Field(
        default=["http://localhost:3000"],
        alias="CORS_ORIGINS",
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

    @field_validator(
        "content_ege_db_path",
        "content_oge_db_path",
        "content_lectures_db_path",
        mode="before",
    )
    @classmethod
    def resolve_content_path(cls, value: object) -> Path:
        path = Path(value) if not isinstance(value, Path) else value
        if not path.is_absolute():
            path = (_MONOREPO_ROOT / "backend" / path).resolve()
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
