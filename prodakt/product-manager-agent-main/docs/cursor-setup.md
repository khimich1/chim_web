# PM Skills — установка в Cursor

Этот каталог — upstream [phuryn/pm-skills](https://github.com/phuryn/pm-skills). Для Cursor используй синхронизацию в `.cursor/skills/`.

## Установка / обновление

Из корня репозитория `chim_web`:

```bash
./prodakt/product-manager-agent-main/scripts/sync-to-cursor.sh
```

После sync доступны:
- **65 atomic skills** — фреймворки (PRD, SWOT, personas…)
- **36 workflow skills** — цепочки `pm-workflow-*` (аналог `/discover`, `/write-prd`…)

Документация: [`docs/pm-skills-cursor.md`](../../docs/pm-skills-cursor.md)

Meta-skill: `.cursor/skills/using-pm-skills/SKILL.md`

## Пример использования в Cursor

```
Следуй skill pm-workflow-discover для идеи AI-ассистента для учителей
@.cursor/skills/create-prd/SKILL.md — напиши PRD для SSO
Следуй skill pm-workflow-strategy
```

## Отличия от Claude Code

| Claude Code | Cursor |
|-------------|--------|
| `/discover`, `/strategy` | `pm-workflow-discover`, `pm-workflow-strategy` |
| Plugin marketplace | Скрипт `scripts/sync-to-cursor.sh` |
| Auto-load skills | По `description` в frontmatter |

## Структура upstream

```
pm-product-discovery/   # skills/ + commands/ + .claude-plugin/
pm-product-strategy/
pm-execution/
pm-market-research/
pm-data-analytics/
pm-go-to-market/
pm-marketing-growth/
pm-toolkit/
scripts/sync-to-cursor.sh   # адаптация для Cursor (этот репо)
```
