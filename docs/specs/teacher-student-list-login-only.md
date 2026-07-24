# Spec: Список учеников — только логин

**Версия:** 0.1.0  
**Дата:** 2026-07-23  
**Статус:** реализовано (2026-07-23)  
**Родитель:** [`student-login-identifier.md`](student-login-identifier.md) US-LI-5; [`teacher-cabinet-ux.md`](teacher-cabinet-ux.md) §8.2  
**Scope:** колонка «Ученик» в таблице списка преподавателя. Без изменений API, лидерборда, публичных имён.

---

## Assumptions

Если не поправите — считаем принятыми:

1. **В таблице `/teacher/students` показываем только логин** (`student.email`) — одной строкой, обычным весом текста.
2. **Убираем верхнюю строку** с `display_name` / сгенерированным `Ученик-{uuid8}` (`resolvePublicDisplayName`).
3. **Кастомный ник ученика** (напр. «Аня») в этом списке **не показываем** — преподаватель оперирует логином для входа/поддержки. Ник остаётся для лидерборда/публичных мест.
4. **Заголовок колонки** остаётся «Ученик» (не переименовываем в «Логин» в этом срезе).
5. **`resolvePublicDisplayName`** и лидерборд **не трогаем**.
6. **Backend / API** без изменений.

→ Поправьте сейчас, иначе после OK реализуем с этими допущениями.

---

## 1. Objective

### Проблема

В колонке «Ученик» две строки: сверху `Ученик-3f98a34f` (или ник), снизу логин `petrov`. Преподавателю нужен только логин — код UUID шумит и путает.

### Success criteria

- [ ] В `StudentList` нет текста вида `Ученик-xxxxxxxx`.
- [ ] В ячейке виден только `student.email` (логин).
- [ ] Vitest `StudentList.test.tsx` обновлён и зелёный.
- [ ] Лидерборд / `resolvePublicDisplayName` без регрессии (существующие тесты).

---

## 2. Tech Stack

Frontend: Next.js, Vitest. Без новых зависимостей.

---

## 3. Commands

```bash
cd frontend
npm run test -- StudentList
npm run lint
npm run build
```

---

## 4. Project Structure

| Файл | Изменение |
|------|-----------|
| `frontend/components/students/StudentList.tsx` | Убрать `resolvePublicDisplayName`; одна строка = `student.email` |
| `frontend/components/students/StudentList.test.tsx` | Assert логин; не assert ник/«Ученик-» |

---

## 5. Code Style

```tsx
<td className="px-4 py-3 text-zinc-900">{student.email}</td>
```

---

## 6. Testing Strategy

| Уровень | Что |
|---------|-----|
| Vitest | Список показывает логин; нет `Ученик-`; stats-колонки как раньше |
| Manual | `/teacher/students` — одна строка на ученика |

---

## 7. Boundaries

### Always

- Только FE список учеников преподавателя.
- Тесты зелёные перед завершением.

### Ask first

- Показывать ник + логин (две строки) вместо «только логин».
- Rename заголовка колонки → «Логин».
- Менять лидерборд / публичные имена.

### Never

- Менять backend `resolve_public_display_name`.
- Трогать student UX.

---

## 8. Not Doing

- Rename колонки / API `email` → `login`.
- Drawer карточки ученика (если появится позже — отдельный срез).
- Удаление `resolvePublicDisplayName` из репозитория.

---

## 9. Next step (gated)

1. Подтвердите Assumptions 1–6 (особенно #3: ник «Аня» тоже скрываем?).
2. После OK → одна правка `StudentList` + тест.

**Код не пишем**, пока assumptions не подтверждены.
