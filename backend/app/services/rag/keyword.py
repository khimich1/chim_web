"""Keyword/BM25-style scoring for RAG slice 2a (no vector DB)."""

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+")

_RU_STOP_WORDS = frozenset(
    {
        "а",
        "без",
        "более",
        "бы",
        "был",
        "была",
        "были",
        "было",
        "быть",
        "в",
        "вам",
        "вас",
        "ведь",
        "во",
        "вот",
        "все",
        "всего",
        "всех",
        "вы",
        "где",
        "да",
        "даже",
        "для",
        "до",
        "его",
        "ее",
        "ей",
        "ему",
        "если",
        "есть",
        "еще",
        "же",
        "за",
        "здесь",
        "и",
        "из",
        "или",
        "им",
        "их",
        "к",
        "как",
        "какой",
        "когда",
        "ко",
        "который",
        "кроме",
        "ли",
        "либо",
        "мне",
        "может",
        "мы",
        "на",
        "над",
        "надо",
        "наш",
        "не",
        "него",
        "нее",
        "ней",
        "нет",
        "ни",
        "них",
        "но",
        "ну",
        "о",
        "об",
        "однако",
        "он",
        "она",
        "они",
        "оно",
        "от",
        "очень",
        "по",
        "под",
        "при",
        "про",
        "с",
        "со",
        "так",
        "также",
        "такой",
        "там",
        "те",
        "тем",
        "то",
        "того",
        "тоже",
        "той",
        "только",
        "том",
        "ты",
        "у",
        "уже",
        "хотя",
        "чего",
        "чем",
        "через",
        "что",
        "чтобы",
        "чуть",
        "эта",
        "эти",
        "этим",
        "этих",
        "это",
        "этого",
        "этой",
        "этом",
        "этот",
        "эту",
        "я",
    }
)


def tokenize(text: str) -> list[str]:
    """Lowercase tokens with RU/EN letters and digits; drop stop words."""
    tokens = [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]
    return [token for token in tokens if len(token) > 1 and token not in _RU_STOP_WORDS]


def keyword_score(
    query: str,
    *,
    title: str,
    body: str,
    avg_doc_len: float,
    doc_count: int,
) -> float:
    """BM25-lite score with a title boost."""
    query_terms = tokenize(query)
    if not query_terms:
        return 0.0

    title_tokens = tokenize(title)
    body_tokens = tokenize(body)
    if not title_tokens and not body_tokens:
        return 0.0

    title_counts = Counter(title_tokens)
    body_counts = Counter(body_tokens)
    doc_len = len(body_tokens) or 1.0

    k1 = 1.5
    b = 0.75
    title_weight = 2.0
    score = 0.0

    for term in set(query_terms):
        tf = body_counts.get(term, 0) + title_counts.get(term, 0) * title_weight
        if tf == 0:
            continue
        idf = math.log(1 + (doc_count - 1 + 0.5) / (1 + 0.5))
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
        score += idf * tf_norm

    return score
