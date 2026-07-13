"""Pydantic models for textbook_sections.yaml."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

ALLOWED_VIDEO_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "m.youtube.com",
        "vk.com",
        "www.vk.com",
        "vkvideo.ru",
        "www.vkvideo.ru",
    }
)


def validate_video_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme != "https":
        msg = "video_url must use HTTPS"
        raise ValueError(msg)
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_VIDEO_HOSTS:
        msg = f"video_url host not allowed: {host}"
        raise ValueError(msg)
    return cleaned


class TopicConfigEntry(BaseModel):
    topic: str = Field(min_length=1)
    video_url: str | None = None

    @field_validator("video_url")
    @classmethod
    def _validate_video_url(cls, value: str | None) -> str | None:
        return validate_video_url(value)


class SectionConfigEntry(BaseModel):
    title: str = Field(min_length=1)
    topics: list[TopicConfigEntry] = Field(default_factory=list)


class TextbookSectionsFile(BaseModel):
    sections: dict[str, SectionConfigEntry]

    @field_validator("sections")
    @classmethod
    def _require_known_sections(
        cls,
        value: dict[str, SectionConfigEntry],
    ) -> dict[str, SectionConfigEntry]:
        required = {"basics", "elements", "organic"}
        missing = required - set(value)
        if missing:
            msg = f"Missing required sections: {sorted(missing)}"
            raise ValueError(msg)
        return value


class SectionRead(BaseModel):
    section_id: str
    title: str
    topic_count: int
