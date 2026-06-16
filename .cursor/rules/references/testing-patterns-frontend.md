# Testing Patterns — Frontend (Next.js)

Справочник для `test-driven-development` и `frontend-ui-engineering`.
Backend: см. `testing-patterns.md` (pytest/FastAPI).

Стек: **Vitest** + **React Testing Library** + **MSW** + **Playwright**.

## Arrange-Act-Assert

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TaskForm } from './TaskForm';

it('отправляет форму с введённым названием', async () => {
  const user = userEvent.setup();
  const onSuccess = vi.fn();

  render(<TaskForm onSuccess={onSuccess} />);

  await user.type(screen.getByLabelText(/название/i), 'Новая задача');
  await user.click(screen.getByRole('button', { name: /создать/i }));

  expect(onSuccess).toHaveBeenCalledWith(
    expect.objectContaining({ title: 'Новая задача' })
  );
});
```

## Именование

```tsx
describe('TaskForm', () => {
  it('показывает ошибку при пустом названии', () => {});
  it('вызывает onSuccess после успешного POST', () => {});
});
```

## Vitest + RTL queries

```tsx
// Предпочитай accessible queries
screen.getByRole('button', { name: /создать/i });
screen.getByLabelText(/email/i);
screen.getByText(/задача создана/i);

// Избегай
screen.getByTestId('submit-btn');  // только если нет a11y alternative

expect(element).toBeInTheDocument();
expect(element).toBeDisabled();
await expect(screen.findByText(/ошибка/i)).resolves.toBeInTheDocument();
```

## MSW — mock FastAPI

```tsx
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('http://localhost:8000/api/tasks', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      { id: '1', title: body.title, status: 'pending' },
      { status: 201 }
    );
  }),
  http.post('http://localhost:8000/api/tasks', () => {
    return HttpResponse.json(
      { error: { code: 'VALIDATION_ERROR', message: 'Title required' } },
      { status: 422 }
    );
  }),
];

// vitest.setup.ts
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';
export const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Тест api-client

```tsx
import { createTask } from '@/lib/api/tasks';

it('createTask возвращает задачу при 201', async () => {
  const task = await createTask({ title: 'Test' });
  expect(task).toMatchObject({ title: 'Test', status: 'pending' });
});

it('createTask бросает ApiError при 422', async () => {
  server.use(
    http.post('*/api/tasks', () =>
      HttpResponse.json({ error: { code: 'VALIDATION_ERROR' } }, { status: 422 })
    )
  );
  await expect(createTask({ title: '' })).rejects.toMatchObject({ status: 422 });
});
```

## Server Components

Server Components тестируй через:
- Integration/E2E (Playwright) — предпочтительно
- Или extract logic в pure functions + unit test

```tsx
// lib/tasks/format.ts — pure, легко тестировать
export function formatTaskStatus(status: string): string {
  return status === 'pending' ? 'В ожидании' : 'Готово';
}
```

## Playwright E2E

```typescript
// e2e/tasks.spec.ts
import { test, expect } from '@playwright/test';

test('пользователь создаёт задачу', async ({ page }) => {
  await page.goto('http://localhost:3000/tasks');

  await page.getByLabel('Название').fill('Купить молоко');
  await page.getByRole('button', { name: 'Создать' }).click();

  await expect(page.getByText('Купить молоко')).toBeVisible();
});

test('пустое название показывает ошибку', async ({ page }) => {
  await page.goto('http://localhost:3000/tasks/new');
  await page.getByRole('button', { name: 'Создать' }).click();
  await expect(page.getByRole('alert')).toContainText(/название/i);
});
```

Запуск: FastAPI + Next dev, или mock API в CI.

## Mock границы

```
Mock:                         Не mock:
├── fetch к FastAPI (MSW)     ├── formatters, validators UI
├── External services         ├── Presentation components (props in)
└── next/navigation (при нужде) └── utils
```

## Команды

```bash
cd frontend
npm run test              # vitest
npm run test:watch
npm run test:coverage
npm run test:e2e          # playwright
```

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| testId вместо role/label | Accessible queries |
| Snapshot всего дерева | Assert specific text/state |
| Shared mutable state | beforeEach cleanup |
| Mock внутренних utils | Mock API boundary (MSW) |
| E2E для всего | Unit для logic, E2E для critical paths |
| Забыть `await userEvent` | async/await везде |
