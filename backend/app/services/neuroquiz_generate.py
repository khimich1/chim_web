"""Neuroquiz question generation (mock first; real LLM in NQ-7)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import Settings, get_settings
from app.models.enums import NeuroQuizQuestionSource
from app.repositories.content.lectures import LectureContentRepo, SelfCheckQA

logger = logging.getLogger(__name__)

# Bump when distractor/prompt rules change so ensure/warmup retires stale cache.
GENERATION_VERSION = 2


def generation_marker(version: int | None = None) -> str:
    """Stable tag stored in explanation so ensure can detect outdated cache."""
    v = GENERATION_VERSION if version is None else version
    return f"[nq_gen:{v}]"


def explanation_has_current_generation(explanation: str | None) -> bool:
    if not explanation:
        return False
    return generation_marker() in explanation


def attach_generation_marker(explanation: str | None) -> str:
    marker = generation_marker()
    base = (explanation or "").strip()
    if marker in base:
        return base
    if not base:
        return marker
    return f"{base}\n{marker}"


_GEN_MARKER_RE = re.compile(r"\s*\[nq_gen:\d+\]\s*", re.MULTILINE)


def strip_generation_marker(explanation: str | None) -> str | None:
    """Remove cache version tags before returning explanation to clients."""
    if explanation is None:
        return None
    cleaned = _GEN_MARKER_RE.sub("\n", explanation).strip()
    return cleaned or None


@dataclass(frozen=True, slots=True)
class GeneratedMCQ:
    prompt: str
    options: list[dict[str, str]]  # [{id, text}, ...] length 4
    correct_option_id: str
    explanation: str | None
    source: NeuroQuizQuestionSource


class NeuroQuizGenerator(Protocol):
    def generate_for_chunk(
        self,
        *,
        topic: str,
        chunk_idx: int,
        lecture: str,
        qa_pairs: list[SelfCheckQA],
        need: int,
    ) -> list[GeneratedMCQ]:
        """Return up to ``need`` MCQ items for the chunk."""


# Phrases that mark a cached/generated question as low-quality filler.
# Matched case-insensitively as substring against option text.
GENERIC_DISTRACTOR_DENYLIST: tuple[str, ...] = (
    "это не относится к данной теме",
    "не относится к данной теме",
    "не относится к теме",
    "верно только при особых условиях",
    "обратное утверждение",
    "зависит только от температуры",
    "невозможно определить из текста",
    "смесь простых веществ",
    "все вышеперечисленное",
    "все вышеперечисленные",
    "ничего из перечисленного",
    "нет верного ответа",
    "затрудняюсь ответить",
)

# Chemically plausible *false* concept distractors (never meta-filler, never chapter facts).
_CHEMISTRY_FALSE_POOL = [
    "Оксид металла как определение кислоты",
    "Основание без гидроксид-ионов",
    "Кислотный оксид без кислорода",
    "Простое вещество — раствор соли",
    "Молекулярное соединение из одного атома",
    "Ковалентная неполярная связь в NaCl",
    "Металлическая решётка в H2O",
    "Раствор сильного электролита без ионов",
    "Реакция замещения даёт только воду",
    "Реакция разложения всегда даёт соль",
    "Окисление без изменения степеней окисления",
    "Амфотерный гидроксид без металла",
    "Соль слабой кислоты без кислотного остатка",
    "Газообразный водород как определение соли",
    "Каталитический процесс без катализатора как обязательное условие",
    "Ионная связь в молекуле H2",
    "Ковалентная полярная связь в кристалле натрия",
    "Молекулярная решётка у металлического натрия",
    "Слабый электролит полностью диссоциирует",
    "Реакция обмена всегда выделяет водород",
]


def options_have_generic_junk(options: list[Any]) -> bool:
    """True if any option text matches known generic distractor filler."""
    for opt in options:
        text = ""
        if isinstance(opt, dict):
            raw = opt.get("text")
            text = raw if isinstance(raw, str) else ""
        elif isinstance(opt, str):
            text = opt
        lowered = text.strip().lower()
        if not lowered:
            continue
        for phrase in GENERIC_DISTRACTOR_DENYLIST:
            if phrase in lowered:
                return True
    return False


def _norm_fact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def distractors_reuse_true_facts(
    options: list[Any],
    *,
    correct_option_id: str | None,
    true_facts: list[str] | None,
) -> bool:
    """True if a non-correct option equals another known-true fact from the chunk."""
    if not true_facts:
        return False
    fact_keys = {_norm_fact(f) for f in true_facts if f and f.strip()}
    if not fact_keys:
        return False
    for opt in options:
        if not isinstance(opt, dict):
            continue
        oid = opt.get("id")
        text = opt.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        if correct_option_id is not None and oid == correct_option_id:
            continue
        if _norm_fact(text) in fact_keys:
            return True
    return False


def options_reuse_sibling_answers(
    options: list[Any],
    *,
    correct_option_id: str | None,
    sibling_answers: list[str] | None,
) -> bool:
    """Heuristic: distractor text matches another QA answer from the same chunk."""
    return distractors_reuse_true_facts(
        options,
        correct_option_id=correct_option_id,
        true_facts=sibling_answers,
    )


def _option_id(index: int) -> str:
    return chr(ord("a") + index)


def _mutate_correct_to_false(correct: str, *, question: str = "") -> list[str]:
    """Build deliberately false answers by mutating the correct claim."""
    c = correct.strip()
    out: list[str] = []
    formulaish = re.fullmatch(r"[A-Za-z0-9()\[\]·⋅\-+]+", c.replace(" ", ""))
    if formulaish and len(c) <= 24:
        swaps = {
            "NaCl": ["KCl", "Na2O", "HCl"],
            "H2SO4": ["H2SO3", "HNO3", "Na2SO4"],
            "HCl": ["HBr", "NaCl", "Cl2"],
            "H2O": ["H2O2", "CO2", "NH3"],
            "CO2": ["CO", "SO2", "CaCO3"],
            "NaOH": ["KOH", "Ca(OH)2", "NaCl"],
            "CaCO3": ["CaO", "Na2CO3", "CaCl2"],
            "NH3": ["N2", "NO2", "NH4Cl"],
            "O2": ["O3", "H2O", "CO2"],
            "N2": ["NH3", "NO", "N2O"],
        }
        key = c.replace(" ", "")
        if key in swaps:
            out.extend(swaps[key])
        else:
            out.extend(["H2O", "NaCl", "CO2"])

    lowered = c.lower()
    q_lower = question.lower()

    # Wrong ion / antonym swaps
    ion_swaps = [
        ("ионов водорода", "ионов гидроксида"),
        ("ионы водорода", "ионы гидроксида"),
        ("ион водорода", "ион гидроксида"),
        ("h+", "oh−"),
        ("н+", "oh−"),
        ("гидроксид", "водородных ионов"),
        ("oh−", "h+"),
        ("oh-", "h+"),
    ]
    for src, dst in ion_swaps:
        if src in lowered:
            mutated = re.sub(re.escape(src), dst, c, count=1, flags=re.IGNORECASE)
            if mutated.strip().lower() != lowered:
                out.append(mutated)

    # Negate common definition patterns
    negations = [
        (r"содержащ\w*\s+атом\w*\s+водорода", "не содержащее атомов водорода"),
        (r"с\s+атом\w*\s+водорода", "без атомов водорода"),
        (r"ионн\w*\s+соединени\w*", "молекулярное соединение без ионов"),
        (r"металл\w*\s+и\s+кислотн\w*\s+остатк\w*", "неметалл и основный остаток"),
        (r"соль\s+и\s+вода", "только газ без соли"),
        (r"соль\s+и\s+воду", "только водород без соли"),
        (r"нейтрализац\w*", "горения без продуктов"),
    ]
    for pattern, replacement in negations:
        if re.search(pattern, lowered):
            mutated = re.sub(pattern, replacement, c, count=1, flags=re.IGNORECASE)
            if _norm_fact(mutated) != lowered:
                out.append(mutated)

    concept_blob = f"{lowered} {q_lower}"
    if "кислот" in concept_blob:
        out.extend(
            [
                "Основание (гидроксид металла)",
                "Основный оксид",
                "Соль без атомов водорода",
                "Сложное вещество без атомов водорода",
                "Вещество, дающее в растворе ионы OH−",
            ]
        )
    if "основан" in concept_blob or "гидроксид" in concept_blob:
        out.extend(
            [
                "Кислота",
                "Кислотный оксид",
                "Соль без гидроксид-ионов",
                "Вещество, дающее в растворе ионы H+",
            ]
        )
    if "оксид" in concept_blob:
        out.extend(
            [
                "Соль",
                "Основание",
                "Простое вещество",
            ]
        )
    if "соль" in concept_blob or "ионн" in concept_blob:
        out.extend(
            [
                "Молекулярное соединение без ионов",
                "Смесь металла и неметалла без связи",
                "Кислотный оксид как определение соли",
            ]
        )
    if "ковалент" in concept_blob:
        out.extend(
            [
                "Ионная связь",
                "Металлическая связь",
                "Водородная связь как основной тип",
            ]
        )
    if "ионн" in concept_blob and "связ" in concept_blob:
        out.extend(
            [
                "Ковалентная полярная связь",
                "Металлическая связь",
                "Водородная связь",
            ]
        )
    if "нейтрализац" in concept_blob or (
        "соль" in concept_blob and "вод" in concept_blob
    ):
        out.extend(
            [
                "Только водород без соли",
                "Только оксид металла",
                "Смесь кислоты и основания без реакции",
            ]
        )

    # Drop anything that accidentally equals the correct answer
    return [x for x in out if _norm_fact(x) != lowered]


def _stable_distractors(
    seed: str,
    correct: str,
    *,
    forbidden_true_facts: list[str] | None = None,
    topic: str = "",
    question: str = "",
    count: int = 3,
) -> list[str]:
    """Pick chemically plausible *false* options; never sibling chapter truths."""
    del topic  # reserved for future topic-tuned pools
    preferred: list[str] = []
    pool: list[str] = []
    seen_lower: set[str] = {_norm_fact(correct)}
    forbidden = {_norm_fact(f) for f in (forbidden_true_facts or []) if f and f.strip()}
    seen_lower |= forbidden

    def _add(bucket: list[str], text: str) -> None:
        t = text.strip()
        if not t:
            return
        key = _norm_fact(t)
        if key in seen_lower:
            return
        if options_have_generic_junk([{"text": t}]):
            return
        seen_lower.add(key)
        bucket.append(t)

    # Prefer question-specific false mutations, then topic-false pool.
    for ans in _mutate_correct_to_false(correct, question=question):
        _add(preferred, ans)
    for ans in _CHEMISTRY_FALSE_POOL:
        _add(pool, ans)

    out: list[str] = []
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    start = int(digest[:8], 16)

    if preferred:
        for i in range(len(preferred)):
            if len(out) >= count:
                break
            candidate = preferred[(start + i) % len(preferred)]
            if candidate not in out:
                out.append(candidate)

    if pool and len(out) < count:
        i = 0
        n = len(pool)
        while len(out) < count and i < n * 3:
            candidate = pool[(start + i) % n]
            i += 1
            if candidate in out:
                continue
            out.append(candidate)

    pad_i = 0
    while len(out) < count:
        pad = _CHEMISTRY_FALSE_POOL[pad_i % len(_CHEMISTRY_FALSE_POOL)]
        pad_i += 1
        if _norm_fact(pad) not in seen_lower and pad not in out:
            out.append(pad)
            seen_lower.add(_norm_fact(pad))
    return out[:count]


def _shuffle_options(
    texts: list[str],
    seed: str,
) -> tuple[list[dict[str, str]], str]:
    order = sorted(range(len(texts)), key=lambda i: seed[i % len(seed)] + str(i))
    options: list[dict[str, str]] = []
    correct_id = "a"
    for slot, src_idx in enumerate(order):
        oid = _option_id(slot)
        options.append({"id": oid, "text": texts[src_idx]})
        if src_idx == 0:
            correct_id = oid
    return options, correct_id


def _mcq_from_qa(
    pair: SelfCheckQA,
    *,
    forbidden_true_facts: list[str],
    topic: str,
) -> GeneratedMCQ:
    correct = pair.answer.strip()
    distractors = _stable_distractors(
        f"{pair.question}|{correct}",
        correct,
        forbidden_true_facts=forbidden_true_facts,
        topic=topic,
        question=pair.question,
    )
    texts = [correct, *distractors]
    seed = hashlib.md5(pair.question.encode("utf-8")).hexdigest()
    options, correct_id = _shuffle_options(texts, seed)
    return GeneratedMCQ(
        prompt=pair.question.strip(),
        options=options,
        correct_option_id=correct_id,
        explanation=attach_generation_marker(f"Правильный ответ: {correct}"),
        source=NeuroQuizQuestionSource.QA_PAIR,
    )


def _sentences_from_lecture(lecture: str) -> list[str]:
    cleaned = re.sub(r"[#*`_\[\]()]", " ", lecture)
    parts = re.split(r"[.!?!\n]+", cleaned)
    return [p.strip() for p in parts if len(p.strip()) >= 20]


def _mcq_from_lecture(
    topic: str,
    lecture: str,
    index: int,
    *,
    forbidden_true_facts: list[str] | None = None,
) -> GeneratedMCQ:
    sentences = _sentences_from_lecture(lecture)
    if sentences:
        fact = sentences[index % len(sentences)]
        # Prefer a short factual stem over yes/no meta-questions
        prompt = f"Что верно по теме «{topic}»?"
        correct = fact if len(fact) <= 120 else fact[:117] + "…"
    else:
        prompt = f"Какое утверждение лучше описывает тему «{topic}»?"
        correct = f"Основное содержание связано с темой «{topic}»"
        fact = topic
    distractors = _stable_distractors(
        f"lec|{topic}|{index}|{fact}",
        correct,
        forbidden_true_facts=forbidden_true_facts or [],
        topic=topic,
        question=prompt,
    )
    texts = [correct, *distractors]
    seed = hashlib.md5(f"{topic}:{index}:{fact}".encode()).hexdigest()
    options, correct_id = _shuffle_options(texts, seed)
    return GeneratedMCQ(
        prompt=prompt,
        options=options,
        correct_option_id=correct_id,
        explanation=attach_generation_marker("Опирайтесь на текст чанка."),
        source=NeuroQuizQuestionSource.LECTURE_GEN,
    )


def validate_mcq_payload(
    raw: dict[str, Any],
    *,
    source: NeuroQuizQuestionSource,
    true_facts: list[str] | None = None,
) -> GeneratedMCQ | None:
    """Validate one MCQ dict from LLM/mock into GeneratedMCQ; None if invalid."""
    prompt = raw.get("prompt")
    options = raw.get("options")
    correct_option_id = raw.get("correct_option_id")
    explanation = raw.get("explanation")
    if not isinstance(prompt, str) or not prompt.strip():
        return None
    if not isinstance(options, list) or len(options) != 4:
        return None
    parsed_opts: list[dict[str, str]] = []
    ids: set[str] = set()
    for opt in options:
        if not isinstance(opt, dict):
            return None
        oid = opt.get("id")
        text = opt.get("text")
        if not isinstance(oid, str) or not isinstance(text, str):
            return None
        if not oid.strip() or not text.strip() or oid in ids:
            return None
        ids.add(oid)
        parsed_opts.append({"id": oid, "text": text.strip()})
    if not isinstance(correct_option_id, str) or correct_option_id not in ids:
        return None
    # Reject generic filler distractors (and any option text matching denylist)
    if options_have_generic_junk(parsed_opts):
        return None
    # Reject distractors that equal other true facts from the same chunk/passage
    if distractors_reuse_true_facts(
        parsed_opts,
        correct_option_id=correct_option_id,
        true_facts=true_facts,
    ):
        return None
    expl = (
        explanation.strip()
        if isinstance(explanation, str) and explanation.strip()
        else None
    )
    return GeneratedMCQ(
        prompt=prompt.strip(),
        options=parsed_opts,
        correct_option_id=correct_option_id,
        explanation=attach_generation_marker(expl),
        source=source,
    )


class MockNeuroQuizGenerator:
    """Deterministic hybrid C1 without calling an LLM (NQ-2)."""

    def generate_for_chunk(
        self,
        *,
        topic: str,
        chunk_idx: int,
        lecture: str,
        qa_pairs: list[SelfCheckQA],
        need: int,
    ) -> list[GeneratedMCQ]:
        del chunk_idx
        if need <= 0:
            return []
        items: list[GeneratedMCQ] = []
        all_answers = [p.answer.strip() for p in qa_pairs if p.answer.strip()]
        for pair in qa_pairs:
            if len(items) >= need:
                break
            # Other QA answers are true facts — never use them as distractors.
            forbidden = [a for a in all_answers if a != pair.answer.strip()]
            items.append(
                _mcq_from_qa(pair, forbidden_true_facts=forbidden, topic=topic)
            )
        pad_i = 0
        while len(items) < need:
            items.append(
                _mcq_from_lecture(
                    topic,
                    lecture,
                    pad_i,
                    forbidden_true_facts=all_answers,
                )
            )
            pad_i += 1
        return items


class LlmNeuroQuizGenerator:
    """Hybrid C1 via ChatOpenAI-compatible API; falls back to mock on failure."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        llm: Any | None = None,
        fallback: NeuroQuizGenerator | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._llm = llm
        self._fallback = fallback or MockNeuroQuizGenerator()

    def _get_llm(self) -> Any | None:
        if self._llm is not None:
            return self._llm
        api_key = self._settings.effective_llm_api_key
        if not api_key:
            return None
        try:
            from langchain_openai import ChatOpenAI
            from pydantic import SecretStr
        except ImportError:
            logger.warning("langchain-openai missing; neuroquiz uses mock generator")
            return None
        base_url = self._settings.effective_llm_base_url or None
        return ChatOpenAI(
            model=self._settings.effective_llm_model,
            temperature=0.2,
            api_key=SecretStr(api_key),
            base_url=base_url,
        )

    def generate_for_chunk(
        self,
        *,
        topic: str,
        chunk_idx: int,
        lecture: str,
        qa_pairs: list[SelfCheckQA],
        need: int,
    ) -> list[GeneratedMCQ]:
        if need <= 0:
            return []
        llm = self._get_llm()
        if llm is None:
            return self._fallback.generate_for_chunk(
                topic=topic,
                chunk_idx=chunk_idx,
                lecture=lecture,
                qa_pairs=qa_pairs,
                need=need,
            )
        try:
            items = self._generate_with_llm(
                llm,
                topic=topic,
                lecture=lecture,
                qa_pairs=qa_pairs,
                need=need,
            )
            if len(items) < need:
                pad = self._fallback.generate_for_chunk(
                    topic=topic,
                    chunk_idx=chunk_idx,
                    lecture=lecture,
                    qa_pairs=qa_pairs,
                    need=need - len(items),
                )
                items.extend(pad)
            return items[:need]
        except Exception:
            logger.exception("Neuroquiz LLM generation failed; using mock")
            return self._fallback.generate_for_chunk(
                topic=topic,
                chunk_idx=chunk_idx,
                lecture=lecture,
                qa_pairs=qa_pairs,
                need=need,
            )

    def _generate_with_llm(
        self,
        llm: Any,
        *,
        topic: str,
        lecture: str,
        qa_pairs: list[SelfCheckQA],
        need: int,
    ) -> list[GeneratedMCQ]:
        qa_block = "\n".join(
            f"- Q: {p.question}\n  A: {p.answer}" for p in qa_pairs[:need]
        ) or "(нет готовых qa-пар)"
        true_facts = [p.answer.strip() for p in qa_pairs if p.answer.strip()]
        # Also pull short «Важно»-style claims from lecture for validation
        for sent in _sentences_from_lecture(lecture)[:12]:
            if sent not in true_facts:
                true_facts.append(sent)
        lecture_excerpt = lecture[:4000]
        deny = ", ".join(f"«{p}»" for p in GENERIC_DISTRACTOR_DENYLIST[:8])
        facts_block = "\n".join(f"- {f}" for f in true_facts[:20]) or "(нет)"
        prompt = f"""Ты составляешь мини-квиз по химии для ученика.
Тема: {topic}
Текст чанка:
\"\"\"{lecture_excerpt}\"\"\"

Известные пары вопрос-ответ:
{qa_block}

Известные верные факты из чанка (НЕ используй их как неверные варианты):
{facts_block}

Верни JSON-массив ровно из {need} объектов MCQ. Каждый объект:
{{
  "prompt": "текст вопроса",
  "options": [{{"id":"a","text":"..."}},{{"id":"b","text":"..."}},{{"id":"c","text":"..."}},{{"id":"d","text":"..."}}],
  "correct_option_id": "a|b|c|d",
  "explanation": "кратко: почему верный верен; почему каждый distractor ЛОЖЕН для этого вопроса",
  "source": "qa_pair" или "lecture_gen"
}}

Правила (критично):
1. Сформулируй ясный вопрос, опирающийся на текст чанка / qa-пару.
2. Правильный ответ ОБЯЗАН браться из текста (qa_answer или короткая дословная/почти дословная формулировка из лекции).
3. Ровно 4 варианта; ровно один верный.
4. Три distractors должны быть НАМЕРЕННО ЛОЖНЫМИ именно для ЭТОГО вопроса
   (неверное определение, неверная формула, неверный продукт, перевёрнутая причина, типичное заблуждение).
5. ЗАПРЕЩЕНО брать другие верные факты из того же чанка/главы как «неверные» варианты
   (даже если они звучат правдоподобно — для ученика это нечестный квиз).
6. Distractors могут звучать правдоподобно, но фактчески быть неверным ответом на вопрос.
7. По стилю и длине distractors близки к правильному ответу (термин/формула/утверждение того же типа).
8. ЗАПРЕЩЕНЫ шаблонные заглушки вроде: {deny}, «все вышеперечисленное» и т.п.
9. Не пиши meta-варианты («не из текста», «зависит от условий») — пиши конкретные химические понятия/формулы/утверждения.
10. В explanation кратко укажи, почему каждый distractor ложен для данного вопроса.
11. Без markdown вокруг JSON.
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            content = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )
        text = str(content).strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        if not isinstance(data, list):
            return []
        out: list[GeneratedMCQ] = []
        for raw in data:
            if not isinstance(raw, dict):
                continue
            source_raw = raw.get("source")
            source = (
                NeuroQuizQuestionSource.QA_PAIR
                if source_raw == "qa_pair"
                else NeuroQuizQuestionSource.LECTURE_GEN
            )
            item = validate_mcq_payload(
                raw,
                source=source,
                true_facts=true_facts,
            )
            if item is not None:
                out.append(item)
        return out


def build_neuroquiz_generator(settings: Settings | None = None) -> NeuroQuizGenerator:
    """Prefer LLM when API key configured; otherwise deterministic mock."""
    settings = settings or get_settings()
    if settings.llm_configured:
        return LlmNeuroQuizGenerator(settings)
    return MockNeuroQuizGenerator()


def load_chunk_context(
    lectures: LectureContentRepo,
    topic: str,
    chunk_idx: int,
) -> tuple[str, list[SelfCheckQA]] | None:
    chunk = lectures.get_chunk(topic, chunk_idx)
    if chunk is None:
        resolved = lectures.resolve_topic_name(topic)
        if resolved is None:
            return None
        chunk = lectures.get_chunk(resolved, chunk_idx)
        if chunk is None:
            return None
    qa_all = lectures.get_selfcheck_for_topic(chunk.topic)
    qa_chunk = [q for q in qa_all if q.chunk_idx == chunk_idx]
    return chunk.lecture, qa_chunk
