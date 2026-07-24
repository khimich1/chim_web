# Orchestration Patterns (Cursor)

Паттерны оркестрации для Cursor (Composer + Grok). Полная платформенная справка: [cursor-platform.md](cursor-platform.md).

**Главное правило:** пользователь или главная Agent-сессия — оркестратор. Persona не вызывает persona. Skills — обязательные hops.

## Pattern 1: Direct skill invocation

Один skill, одна перспектива, один артефакт.

```
Пользователь: «Следуй skill test-driven-development для этого endpoint»
→ Agent читает SKILL.md → выполняет workflow
```

**Когда:** задача однозначно попадает в один skill.

## Pattern 2: Skill + persona prompt

Skill задаёт процесс; persona задаёт формат вывода.

```
Пользователь: «Review diff по code-reviewer и security-auditor»
→ Agent: code-review-and-quality skill + содержимое agents/*.md
```

**Когда:** нужен стандартный review framework проекта.

## Pattern 3: Parallel fan-out (Task)

Несколько subagents на одном артефакте → синтез в главной сессии.

```
Один assistant turn:
  Task(bugbot / code-reviewer prompt)
  Task(security-review)
  Task(generalPurpose + test-engineer.md)
→ Merge findings → verdict
```

**Когда:**
- [ ] Каждый subagent даёт *разный тип* finding
- [ ] Артефакт один (diff, spec, migration plan)
- [ ] Главная сессия сделает merge, а не делегирует merge subagent'у

**Cursor constraint:** несколько `Task` в **одном сообщении** для параллельности.

## Pattern 4: Sequential lifecycle (user-driven)

Пользователь ведёт цепочку skills, контекст несёт git / SPEC / plan:

```
spec-driven-development → planning-and-task-breakdown
→ incremental-implementation (срез за срезом)
→ test-driven-development → code-review-and-quality → shipping-and-launch
```

Нет автоматического orchestrator — пользователь явно переключает фазу.

## Pattern 5: Explore for research

Read-heavy reconnaissance без записи в код:

```
Task(subagent_type=explore, prompt="Найди все usages of X, thoroughness: medium")
→ Digest в главной сессии → решение → implement skill
```

**Когда:** нужно быстро понять codebase/API перед изменением.

## Pattern 6: Cross-model second opinion

После single-model review (Composer):

1. Предложить пользователю: Task с `model: cursor-grok-4.5-high`, новый чат на Grok, или skip
2. Передать только ARTIFACT + CONTRACT (не рассуждения автора)
3. RECONCILE findings в главной сессии

**Когда:** doubt-driven-development, high-stakes decisions.

## Anti-patterns

### A. Router persona

Persona решает, какую другую persona вызвать → дублирует `using-agent-skills` + intent mapping в `AGENTS.md`.

### B. Persona calls persona

Subagent/persona не запускает другой Task. Recommend follow-up → пользователь или главная сессия.

### C. Nested Task from subagent

Doubt-driven и parallel review — только из главной сессии. Из subagent: эскалация или degraded self-review с пометкой.

### D. Deep delegation trees

Максимальная глубина: главная сессия → Task(s) → merge в главной. Не Task → Task → Task.

## Decision tree

```
Нужен workflow?
  → Есть skill? → Read .cursor/skills/<name>/SKILL.md
  → Нужно несколько перспектив на один diff?
       → Parallel Task (Pattern 3)
  → Нужно второе мнение другой модели?
       → Cross-model (Pattern 6), пользователь решает
  → Только исследование?
       → explore subagent (Pattern 5)
  → Последовательная фича?
       → User-driven lifecycle (Pattern 4)
```
