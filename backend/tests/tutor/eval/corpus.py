"""Synthetic lecture corpus and eval questions for RAG recall@5 (Task 41.3)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ExamTrack = Literal["ege", "oge"]
SourceFilter = Literal["lecture", "lecture_qa"] | None


@dataclass(frozen=True, slots=True)
class LectureChunk:
    topic: str
    chunk_idx: int
    chunk_title: str
    lecture: str
    qa_questions: list[str] | None = None
    qa_answers: list[str] | None = None


@dataclass(frozen=True, slots=True)
class EvalCase:
    query: str
    topic: str
    chunk_idx: int
    track: ExamTrack = "ege"
    source: SourceFilter = None


EVAL_LECTURE_CHUNKS: tuple[LectureChunk, ...] = (
    LectureChunk(
        "Карбоновые кислоты",
        1,
        "Свойства и изомерия карбоновых кислот",
        "Изомерия карбоновых кислот и физические свойства насыщенных кислот.",
    ),
    LectureChunk(
        "Карбоновые кислоты",
        2,
        "Получение карбоновых кислот",
        "### Химические свойства\n\n"
        "Кислоты реагируют с основаниями; типичны для карбоновых соединений.",
    ),
    LectureChunk(
        "Алканы",
        0,
        "Строение и номенклатура",
        "# Алканы\n\nОбщая формула алканов CnH2n+2; насыщенные углеводороды.",
    ),
    LectureChunk(
        "Алканы",
        1,
        "Химические свойства алканов",
        "### Реакции алканов\n\nАлканы малореакционны из-за прочных связей C-C и C-H.",
        qa_questions=["Почему алканы малореакционны?"],
        qa_answers=["Из-за неполярных связей и отсутствия реакционного центра."],
    ),
    LectureChunk(
        "Алкены",
        0,
        "Строение алкенов",
        "Алкены — непредельные углеводороды с двойной связью C=C.",
    ),
    LectureChunk(
        "Алкены",
        1,
        "Реакции присоединения",
        "### Реакции присоединения\n\nПо двойной связи алкены вступают в реакции присоединения.",
    ),
    LectureChunk(
        "Спирты",
        0,
        "Классификация спиртов",
        "Спирты делятся на одноатомные и многоатомные; первичные, вторичные и третичные.",
    ),
    LectureChunk(
        "Спирты",
        1,
        "Получение этанола",
        "### Гидратация алкенов\n\nЭтанол получают гидратацией этилена в присутствии катализатора.",
    ),
    LectureChunk(
        "Фенол",
        0,
        "Свойства фенола",
        "Кислотность фенола: слабее карбоновых кислот, но кислее спиртов.",
    ),
    LectureChunk(
        "Амины",
        0,
        "Основные свойства аминов",
        "Амины проявляют основные свойства и образуют соли с кислотами.",
    ),
    LectureChunk(
        "Альдегиды",
        0,
        "Окисление альдегидов",
        "Альдегиды окисляются до карбоновых кислот; типична реакция серебряного зеркала.",
    ),
    LectureChunk(
        "Углеводы",
        0,
        "Моносахариды",
        "Глюкоза и фруктоза — моносахариды; формула глюкозы C6H12O6.",
    ),
    LectureChunk(
        "Углеводы",
        1,
        "Полисахариды",
        "### Крахмал и целлюлоза\n\nПолисахариды состоят из множества остатков глюкозы.",
    ),
    LectureChunk(
        "Соли",
        0,
        "Ионные соединения",
        "# Соли\n\nИонные соединения образуют кристаллическую решётку из ионов.",
    ),
    LectureChunk(
        "Кислоты",
        0,
        "Сильные и слабые кислоты",
        "Сильные кислоты полностью диссоциируют в воде; слабые — частично.",
    ),
    LectureChunk(
        "Сера",
        0,
        "Элементарная сера",
        "# Сера\n\nЭлементарная сера S — неметалл; сера образует сульфиды с металлами.",
    ),
    LectureChunk(
        "Сера",
        1,
        "Получение и свойства сероводорода",
        "### Реакции серы с металлами\n\n"
        "При нагревании сера реагирует с металлами:\n"
        "S + Cu = CuS\n"
        "S + Ca = CaS\n"
        "Образуются сульфиды металлов.",
    ),
)


EVAL_CASES: tuple[EvalCase, ...] = (
    EvalCase(
        "химические свойства карбоновых кислот",
        "Карбоновые кислоты",
        2,
    ),
    EvalCase(
        "изомерия карбоновых кислот",
        "Карбоновые кислоты",
        1,
    ),
    EvalCase(
        "почему алканы малореакционны",
        "Алканы",
        1,
    ),
    EvalCase(
        "общая формула алканов",
        "Алканы",
        0,
    ),
    EvalCase(
        "реакции присоединения по двойной связи",
        "Алкены",
        1,
    ),
    EvalCase(
        "алкены непредельные углеводороды двойная связь",
        "Алкены",
        0,
    ),
    EvalCase(
        "как получить этанол из этилена",
        "Спирты",
        1,
    ),
    EvalCase(
        "классификация спиртов первичные вторичные",
        "Спирты",
        0,
    ),
    EvalCase(
        "кислотность фенола по сравнению со спиртами",
        "Фенол",
        0,
    ),
    EvalCase(
        "основные свойства аминов",
        "Амины",
        0,
    ),
    EvalCase(
        "реакция серебряного зеркала с альдегидами",
        "Альдегиды",
        0,
    ),
    EvalCase(
        "моносахариды глюкоза формула C6H12O6",
        "Углеводы",
        0,
    ),
    EvalCase(
        "из чего состоит крахмал",
        "Углеводы",
        1,
    ),
    EvalCase(
        "ионная кристаллическая решётка солей",
        "Соли",
        0,
    ),
    EvalCase(
        "чем отличаются сильные кислоты от слабых",
        "Кислоты",
        0,
        track="oge",
    ),
    EvalCase(
        "как с металлами реагирует сера?",
        "Сера",
        1,
    ),
)


def create_eval_lectures_db(path: Path) -> None:
    """Write the eval corpus into a temporary SQLite lectures database."""
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE prepared_lectures (
            topic TEXT NOT NULL,
            chunk_idx INTEGER NOT NULL,
            chunk_title TEXT,
            lecture TEXT,
            qa_questions TEXT,
            qa_answers TEXT,
            PRIMARY KEY (topic, chunk_idx)
        )
        """
    )
    rows = [
        (
            chunk.topic,
            chunk.chunk_idx,
            chunk.chunk_title,
            chunk.lecture,
            json.dumps(chunk.qa_questions, ensure_ascii=False)
            if chunk.qa_questions
            else None,
            json.dumps(chunk.qa_answers, ensure_ascii=False) if chunk.qa_answers else None,
        )
        for chunk in EVAL_LECTURE_CHUNKS
    ]
    conn.executemany(
        """
        INSERT INTO prepared_lectures
            (topic, chunk_idx, chunk_title, lecture, qa_questions, qa_answers)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()
