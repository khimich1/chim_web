"""Static mapping from exam task type → textbook topic (Task 43, tutor-rag §16 open Q1).

v1 uses curated tables per track. Topics must match names in ``prepared_lectures``.
When several topics are listed, the first one present in the textbook wins.
"""

from __future__ import annotations

from app.services.rag.documents import ExamTrack

# EGE: FIPI-style task numbers → lecture topics (approximate curriculum alignment).
_EGE_TYPE_TOPICS: dict[int, tuple[str, ...]] = {
    1: ("Строение атома", "Периодический закон"),
    2: ("Строение атома", "Химическая связь"),
    3: ("Периодический закон", "Металлы"),
    4: ("Химическая связь", "Неметаллы"),
    5: ("Классификация неорганических соединений", "Соли"),
    6: ("ОВР", "Электролиз"),
    7: ("ОВР", "Кислоты"),
    8: ("ОВР", "Основания"),
    9: ("Растворы", "Соли"),
    10: ("Растворы", "ОВР"),
    11: ("Растворы", "Стехиометрия"),
    12: ("Стехиометрия", "Газы"),
    13: ("Органическая химия", "Алканы"),
    14: ("Органическая химия", "Алкены"),
    15: ("Алканы", "Алкены"),
    16: ("Алкены", "Алкины"),
    17: ("Алкины", "Арены"),
    18: ("Алкоголи", "Фенолы"),
    19: ("Альдегиды", "Кетоны"),
    20: ("Карбоновые кислоты", "Сложные эфиры"),
    21: ("Амины", "Аминокислоты"),
    22: ("Углеводы", "Белки"),
    23: ("Полимеры", "Органическая химия"),
    24: ("Органическая химия", "Алканы"),
    25: ("Органическая химия", "Алкены"),
    26: ("Органическая химия", "Алканы"),
    27: ("Органическая химия", "Алкены"),
    28: ("Органическая химия", "Алканы"),
}

# OGE: task file numbers → lecture topics.
_OGE_TYPE_TOPICS: dict[int, tuple[str, ...]] = {
    1: ("Строение атома", "Периодический закон"),
    2: ("Химическая связь", "Классификация неорганических соединений"),
    3: ("ОВР", "Металлы"),
    4: ("ОВР", "Неметаллы"),
    5: ("Соли", "Кислоты"),
    6: ("Растворы", "ОВР"),
    7: ("Растворы", "Стехиометрия"),
    8: ("Стехиометрия", "Газы"),
    9: ("Органическая химия", "Алканы"),
    10: ("Алканы", "Алкены"),
    11: ("Алкены", "Алкины"),
    12: ("Алкоголи", "Карбоновые кислоты"),
    13: ("Органическая химия", "Алканы"),
    14: ("Органическая химия", "Алкены"),
    15: ("Органическая химия", "Алканы"),
    16: ("Органическая химия", "Алкены"),
    17: ("Органическая химия", "Алканы"),
    18: ("Органическая химия", "Алкены"),
    19: ("Органическая химия", "Алканы"),
    20: ("Органическая химия", "Алкены"),
    21: ("Органическая химия", "Алканы"),
    22: ("Органическая химия", "Алкены"),
    23: ("Органическая химия", "Алканы"),
    24: ("Органическая химия", "Алкены"),
}


def mapped_topics_for_type(track: ExamTrack, task_type: int) -> tuple[str, ...]:
    """Return candidate textbook topics for an exam task type."""
    table = _EGE_TYPE_TOPICS if track == "ege" else _OGE_TYPE_TOPICS
    return table.get(task_type, ("Органическая химия",))


def resolve_topic_for_type(
    track: ExamTrack,
    task_type: int,
    *,
    available_topics: set[str],
) -> str | None:
    """Pick the first mapped topic that exists in the textbook."""
    for topic in mapped_topics_for_type(track, task_type):
        if topic in available_topics:
            return topic
    return None
