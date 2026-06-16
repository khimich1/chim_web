# Accessibility Checklist (WCAG 2.1 AA)

Краткий справочник. Используй с `frontend-ui-engineering`.

## Keyboard Navigation

- [ ] Все interactive элементы доступны через Tab
- [ ] Focus order = visual/logical order
- [ ] Focus visible (outline/ring)
- [ ] Custom widgets: Enter activate, Escape close
- [ ] Нет keyboard traps
- [ ] Skip-to-content link (виден при focus)
- [ ] Modals: trap focus, return on close

## Screen Readers

- [ ] Images: `alt` или `alt=""` для decorative
- [ ] Inputs: `<label>` или `aria-label`
- [ ] Кнопки/ссылки: описательный текст (не «нажмите здесь»)
- [ ] Icon-only buttons: `aria-label`
- [ ] Один `<h1>`, без пропуска уровней
- [ ] Dynamic changes: `aria-live`
- [ ] Tables: `<th scope="...">`

## Visual

- [ ] Contrast ≥ 4.5:1 (text), ≥ 3:1 (large text 18px+)
- [ ] UI components ≥ 3:1 vs background
- [ ] Цвет не единственный индикатор состояния
- [ ] Text 200% zoom без поломки layout
- [ ] Нет flashing >3/sec

## Forms

- [ ] Visible label на каждом input
- [ ] Required — не только цветом
- [ ] Errors: конкретные, связаны с полем (`aria-describedby`)
- [ ] Error state: icon/text/border, не только цвет
- [ ] `autocomplete` где уместно (`email`, `name`)

## Content

- [ ] `<html lang="ru">` или `en`
- [ ] Descriptive `<title>`
- [ ] Links отличимы от текста
- [ ] Touch targets ≥ 44×44px mobile
- [ ] Meaningful empty states

## Next.js / React Patterns

```tsx
// Кнопки — actions
<button type="button" onClick={handleDelete}>Удалить</button>

// Ссылки — navigation
<Link href="/tasks/123">Открыть</Link>

// НЕ div как button
<div onClick={...} />  // BAD

<label htmlFor="email">Email</label>
<input id="email" type="email" required />

<div role="status" aria-live="polite">Сохранено</div>
<div role="alert">Ошибка: укажите название</div>

<dialog aria-modal="true" aria-labelledby="dialog-title">...</dialog>
```

## Testing Tools

```bash
# В frontend/
npm run test:a11y          # если настроен axe в vitest
npx playwright test --grep a11y

# Browser
# Chrome DevTools → Lighthouse → Accessibility
# Chrome DevTools → Elements → Accessibility tree
```

Screen readers: NVDA (Windows), VoiceOver (macOS).

## ARIA Live Regions

| Value | Поведение | Для |
|-------|-----------|-----|
| `aria-live="polite"` | При паузе | Status, saved |
| `aria-live="assertive"` | Сразу | Errors |
| `role="status"` | = polite | Confirmations |
| `role="alert"` | = assertive | Validation errors |

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| `div` as button | `<button>` |
| Missing `alt` | Descriptive `alt` |
| Color-only state | Icon + text |
| No focus outline | Style, don't remove |
| `tabindex > 0` | `0` or `-1` only |
| Custom select без ARIA | Native `<select>` or listbox pattern |
