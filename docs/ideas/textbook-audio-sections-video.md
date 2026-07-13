# Учебник: скорость аудио, разделы, видео

**Проект:** `chim_web`  
**Дата:** 2026-06-22  
**Статус:** идея согласована → формализация в [`SPEC.md`](../../SPEC.md) §1.12, план — Phase 18 (`tasks/plan.md`, Tasks 101–104)

**Связано:** idea-refine сессия 2026-06-22; mapping тем по папкам преподавателя (начала химии / химия элементов / органика).

---

## Problem Statement

**Как улучшить учебник для ученика: управляемая скорость озвучки, три логических раздела по программе курса и опциональное видео без перегрузки инфраструктуры?**

---

## Recommended Direction

1. **Audio speed:** пресеты **0.75× / 1× / 1.25× / 1.5×** в кастомном `AudioPlayer`; `HTMLAudioElement.playbackRate`; выбор сохраняется в `localStorage` (`textbook-audio-rate`). Backend не меняется.
2. **Sections:** конфиг `textbook_sections.yaml` (git) → API `section` на темах → UI с тремя section pills на `/student/textbook`. Порядок тем **внутри** раздела — как в БД (`ORDER BY MIN(rowid)`).
3. **Video MVP:** опциональный `video_url` per topic в том же YAML; компонент `VideoEmbed` (YouTube / VK iframe). Self-hosted stream и upload — позже.

---

## Key Assumptions to Validate

- [ ] `playbackRate` стабилен для OGG в Chrome / Safari / mobile.
- [ ] Mapping 31 тем → 3 раздела совпадает с ожиданиями преподавателя (см. SPEC §1.12.2).
- [ ] URL из папок «видео практика» пригодны для embed (публичные YouTube/VK).

---

## MVP Scope

| Срез | Внутри | Снаружи |
|------|--------|---------|
| Task 101 — audio speed | Пресеты + localStorage + vitest | Ползунок произвольной скорости |
| Task 102–103 — sections | YAML + API + UI pills | Новые темы (валентность и др.) |
| Task 104 — video embed | `VideoEmbed` + `video_url` в YAML | Upload MP4, CDN, video в feedback |

---

## Not Doing (and Why)

- **Server-side audio re-encoding** — избыточно; браузерный `playbackRate` достаточен.
- **Колонка `section` в `prepared_lectures.db`** — read-only pipeline; конфиг в git проще на MVP.
- **Self-hosted video CDN** — дорого по egress; embed сначала.
- **Скорость для teacher voice feedback** — отдельная задача, не учебник.

---

## Open Questions

- Финальный порядок тем внутри каждого раздела (сейчас — порядок появления в БД).
- Где хранятся файлы «видео практика» — локально или уже на YouTube/VK?
- Нужен ли отдельный блок «Видео практика» на уровне темы vs одна ссылка на тему?
