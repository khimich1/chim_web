# Spec: Chrome шапки кабинета преподавателя

**Версия:** 0.1.0  
**Дата:** 2026-07-23  
**Статус:** реализовано (2026-07-23)  
**Родитель:** [`teacher-cabinet-ux.md`](teacher-cabinet-ux.md) §8.1, US-TC-1  
**Scope:** только перенос «Выйти» в шапку и устранение дублей «Уведомлений». Без групп, drawer, paste, lightbox.

---

## Assumptions (проверьте до PLAN/IMPLEMENT)

Если не поправите — считаем принятыми:

1. **Единственное место logout** — sticky-шапка `TeacherNav`, правый край (как на скриншоте с зелёной стрелкой).
2. **Колокол в шапке** — `NotificationBell` переносится в `TeacherNav`, слева от «Выйти»; данные prefetch в layout (см. §4).
3. **Nav-ссылка «Уведомления»** (`/teacher/notifications`) **остаётся** — полноценная страница истории; колокол даёт быстрый preview + «Все уведомления».
4. **Текст кнопки колокола** — заменить на **icon-only** (🔔 или SVG) + `aria-label="Уведомления"`, чтобы не дублировать подпись рядом с nav-link «Уведомления».
5. **Удалить с page-headers** на всех `/teacher/*`: `LogoutButton`, `NotificationBell`, блок `flex … gap-3` справа от заголовка (если после удаления там только «На главную» — оставить только эту ссылку).
6. **Главная `/teacher`:** убрать кнопку «Уведомления» из ряда быстрых действий (остаются Ученики, ДЗ, AI-советчик, Конструктор тем). Карточка «Непрочитанные» **остаётся** — это метрика, не навигация.
7. **Студенческий UX** не трогаем — `LogoutButton` на `/student/*` как сейчас.
8. **E2E** `logout()` продолжает кликать единственную кнопку «Выйти» в document (теперь в header).

→ Поправьте пункты 3–4, если хотите оставить текст «Уведомления» на колоколе или убрать nav-link в пользу только колокола.

---

## 1. Objective

### Проблема

На скриншоте и в коде «Выйти» и «Уведомления» живут **в контенте страницы**, хотя в `TeacherNav` уже есть пункт «Уведомления». На главной — **третий** вход (кнопка в ряду действий). Это шум и лишние server-fetch на каждой странице.

### Как должно быть (HMW)

> Как преподаватель, я хочу выход и быстрый доступ к уведомлениям **только в верхней шапке**, чтобы заголовок страницы показывал контекст раздела, а не повторял глобальные действия.

### Success criteria (тестируемые)

- [ ] На любом `/teacher/*` ровно **одна** кнопка «Выйти» — в правом углу `TeacherNav`.
- [ ] На любом `/teacher/*` ровно **один** колокол (icon + badge), в шапке слева от «Выйти».
- [ ] Nav содержит ссылку «Уведомления» на `/teacher/notifications`.
- [ ] Ни на одной teacher-странице нет `NotificationBell` / `LogoutButton` в `<main>`.
- [ ] На `/teacher` нет кнопки «Уведомления» в блоке быстрых действий.
- [ ] `npm run test` — `TeacherNav.test.tsx` покрывает bell + logout; e2e logout зелёный.
- [ ] `npm run build` без ошибок.

---

## 2. Tech Stack

Без новых зависимостей. Next.js App Router, существующие `LogoutButton`, `NotificationBell`, server helpers из `@/lib/api/server`.

---

## 3. Commands

```bash
cd frontend
npm run dev
npm run test -- TeacherNav
npm run test:e2e   # если есть сценарии с logout
npm run lint
npm run build
```

---

## 4. Project Structure

| Файл | Изменение |
|------|-----------|
| `components/layout/TeacherNav.tsx` | + `TeacherNavActions` (client): bell + logout; layout header: brand \| nav \| actions |
| `app/teacher/layout.tsx` | Prefetch `getNotifications()` (slice 5) + `getNotificationUnreadCount()`; передать в nav |
| `app/teacher/page.tsx` | Убрать bell/logout; убрать кнопку «Уведомления» из actions |
| `app/teacher/homework/page.tsx` | Убрать bell/logout (+ лишние fetch если только для bell) |
| `app/teacher/themes/page.tsx` | То же |
| Остальные `app/teacher/**/page.tsx` | Убрать `LogoutButton` из page header |
| `components/notifications/NotificationBell.tsx` | Icon-only trigger (optional в этом срезе) |
| `components/layout/TeacherNav.test.tsx` | Assert bell + logout в header |
| `e2e/helpers/auth.ts` | Без изменений, если один «Выйти» |

**Не трогаем:** `app/student/**`, backend, rename «Темы» → «Конструктор».

---

## 5. Code Style

Layout шапки (ориентир):

```tsx
<header className="sticky top-0 z-30 …">
  <div className="mx-auto flex max-w-5xl … sm:justify-between">
    <BrandLogo />
    <nav>…NAV_LINKS…</nav>
    <div className="flex items-center gap-2 sm:ml-auto">
      <NotificationBell … />
      <LogoutButton />
    </div>
  </div>
</header>
```

- Prefetch notifications в **server** `TeacherLayout`, props в client wrapper — как сейчас на dashboard.
- Не дублировать fetch на каждой child page.

---

## 6. Testing Strategy

| Уровень | Что |
|---------|-----|
| Vitest | `TeacherNav` рендерит logout + bell; nav links на месте |
| Vitest | `NotificationBell` — обновить если меняется label (icon + aria) |
| Manual | Все teacher routes: один logout, нет дубля bell в main |
| Playwright | `logout()` с любой teacher-страницы |

Backend-тесты не нужны.

---

## 7. Boundaries

### Always

- Один logout / один bell на teacher chrome.
- `aria-label` на icon-only bell.
- Удалить неиспользуемые imports и server fetches после переноса.

### Ask first

- Убрать nav-link «Уведомления» (оставить только bell).
- Менять студенческий header аналогично.

### Never

- Два «Выйти» в DOM одновременно.
- JWT / auth logic менять.

---

## 8. UI wireframe (целевое)

```
┌─────────────────────────────────────────────────────────────────┐
│ 🧪 Химия   Главная Ученики Темы Задания Уведомления    🔔(3) Выйти │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ КАБИНЕТ ПРЕПОДАВАТЕЛЯ                                           │
│ teacher@example.com                                             │
│ [карточки метрик]                                               │
│ [Ученики] [Домашние задания] [AI-советчик] [Конструктор тем]    │
└─────────────────────────────────────────────────────────────────┘
```

**Убрано:** bell + logout справа от email; кнопка «Уведомления» в ряду действий.

---

## 9. Not Doing (этот срез)

- Rename «Темы» → «Конструктор» — отдельный срез parent spec.
- Student header unification.
- Badge unread на nav-link вместо bell.
- SSR polling / realtime notifications.

---

## 10. Open Questions

| # | Вопрос | Default если молчите |
|---|--------|----------------------|
| Q1 | Оставляем nav-link «Уведомления» + bell или только bell? | Оба (assumption 3) |
| Q2 | Icon-only bell или текст «Уведомления» на кнопке? | Icon-only (assumption 4) |
| Q3 | Убирать «На главную» с подстраниц? | Нет, вне scope |

---

## 11. Next step (gated)

1. **Вы подтверждаете Assumptions 1–8** (или правите Q1–Q2).
2. После OK → реализация одним инкрементом (~5–8 файлов) + vitest.
3. Полный `teacher-cabinet-ux.md` остаётся roadmap для следующих срезов.

**Production-код не пишем**, пока assumptions не подтверждены.
