"""Load and validate textbook section mapping from YAML."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.schemas.textbook_sections import TextbookSectionsFile


class TextbookSectionsConfigError(Exception):
    """Raised when YAML is invalid or inconsistent with lecture DB topics."""


@dataclass(frozen=True, slots=True)
class TopicSectionMeta:
    section_id: str
    video_url: str | None = None


class TextbookSectionsConfig:
    def __init__(self, config_path: Path, db_topics: set[str]) -> None:
        self._section_titles: dict[str, str] = {}
        self._section_order: list[str] = []
        self._topic_meta: dict[str, TopicSectionMeta] = {}
        self._load(config_path, db_topics)

    @property
    def section_order(self) -> list[str]:
        return list(self._section_order)

    def section_title(self, section_id: str) -> str:
        return self._section_titles[section_id]

    def topic_meta(self, topic: str) -> TopicSectionMeta | None:
        return self._topic_meta.get(topic)

    def list_sections(self) -> list[tuple[str, str, int]]:
        counts: dict[str, int] = {section_id: 0 for section_id in self._section_order}
        for meta in self._topic_meta.values():
            counts[meta.section_id] += 1
        return [
            (section_id, self._section_titles[section_id], counts[section_id])
            for section_id in self._section_order
        ]

    def _load(self, config_path: Path, db_topics: set[str]) -> None:
        if not config_path.is_file():
            msg = f"Textbook sections config not found: {config_path}"
            raise TextbookSectionsConfigError(msg)

        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            parsed = TextbookSectionsFile.model_validate(raw)
        except (OSError, yaml.YAMLError, ValidationError) as exc:
            msg = f"Invalid textbook sections config: {exc}"
            raise TextbookSectionsConfigError(msg) from exc

        yaml_topics: set[str] = set()
        duplicate_topics: set[str] = set()

        for section_id in ("basics", "elements", "organic"):
            section = parsed.sections[section_id]
            self._section_titles[section_id] = section.title
            self._section_order.append(section_id)

            for entry in section.topics:
                if entry.topic in yaml_topics:
                    duplicate_topics.add(entry.topic)
                yaml_topics.add(entry.topic)
                self._topic_meta[entry.topic] = TopicSectionMeta(
                    section_id=section_id,
                    video_url=entry.video_url,
                )

        if duplicate_topics:
            msg = f"Duplicate topics in YAML: {sorted(duplicate_topics)}"
            raise TextbookSectionsConfigError(msg)

        unknown_in_yaml = yaml_topics - db_topics
        if unknown_in_yaml:
            msg = f"Topics in YAML missing from DB: {sorted(unknown_in_yaml)}"
            raise TextbookSectionsConfigError(msg)

        missing_in_yaml = db_topics - yaml_topics
        if missing_in_yaml:
            msg = f"DB topics missing from YAML: {sorted(missing_in_yaml)}"
            raise TextbookSectionsConfigError(msg)


@lru_cache(maxsize=8)
def _cached_config(config_path: str, db_topics_key: tuple[str, ...]) -> TextbookSectionsConfig:
    return TextbookSectionsConfig(Path(config_path), set(db_topics_key))


def get_textbook_sections_config(
    config_path: Path,
    db_topics: set[str],
) -> TextbookSectionsConfig:
    return _cached_config(str(config_path.resolve()), tuple(sorted(db_topics)))
