# Spec: Логин ученика (идентификатор вместо email в UI)

**Версия:** 0.1.0  
**Дата:** 2026-07-23  
**Статус:** черновик — ждёт ревью человека (фаза SPECIFY)  
**Источник:** [`docs/ideas/student-login-identifier.md`](../ideas/student-login-identifier.md)  
**Родитель:** [`SPEC.md`](../../SPEC.md) §3 (Auth), §4 (Онбординг ученика)  
**Связано:** [`docs/specs/teacher-cabinet-ux.md`](teacher-cabinet-ux.md) (форма «Добавить», карточка ученика), multi-teacher isolation

---

## Assumptions (проверьте до PLAN)

Если не поправите — считаем принятыми:

1. **Колонка и JSON-поле остаются `email`** в БД/API на MVP. В UI и пользовательских текстах везде **«логин»**. Rename `email` → `login` — отдельный техдолг, не этот релиз.
2. **Длина логина:** `3…64` символа после `strip` (не 320). Колонка БД `String(320)` не меняем.
3. **Алфавит:** только ASCII-латиница и цифры плюс `._@+-`. Кириллица, пробелы, прочие unicode — **422**.
4. **`@` разрешён** (email-подобные логины вроде `masha@school.ru` валидны).
5. **Нормализация:** `strip().lower()` при **создании/revive** ученика и при **authenticate** (login). `Masha` ≡ `masha`.
6. **One-shot data fix:** Alembic data migration `UPDATE users SET email = lower(email) WHERE email <> lower(email)` (или эквивалент), чтобы case-insensitive вход работал для уже существующих аккаунтов. Коллизии после lower (редко) — остановить миграцию / ручной фикс; в plan заложить проверку.
7. **Hint** под полем создания: «Только латиница, например `ivanov`» (и при желании кратко: можно с `@`).
8. **Один экран входа** для teacher и student: label «Логин», без `type="email"`. Учителя продолжают входить своими текущими идентификаторами (уже латиница/email).
9. **Revive** (из teacher-cabinet-ux): повторный create с тем же логином при `is_active=false` → revive; сравнение после `lower()`.
10. **Валидация формата** — на backend (Pydantic / service). Frontend: `type="text"`, без HTML email-валидации; опционально лёгкая подсказка, не дублировать бизнес-правила жёстко.
11. **Сообщения API** на английском в `detail` (как сейчас: `"Email already registered"` → заменить на login-oriented, напр. `"Login already registered"`); UI мапит на русские строки.
12. **Минимальная длина пароля при установке = 4** (`MIN_PASSWORD_LENGTH`): `StudentCreate` и `seed_teacher` / `--reset-password`. Login по-прежнему принимает любой существующий пароль (`LoginRequest` min 1).

→ Поправьте нумерованные пункты, иначе после approve идём в PLAN с ними.

---

## 1. Objective

### Что строим

Преподаватель заводит ученика по **логину** (латиница, опционально email-подобный), ученик и преподаватель входят по полю **«Логин»**. Идентификатор хранится в `users.email`, нормализуется в lower-case. Восстановление доступа — через преподавателя (уже есть).

### Зачем

Сейчас форма и логин завязаны на «Email» (`type="email"`), хотя у школьников часто нет почты. Backend уже принимает произвольную строку — блокер в основном UX и отсутствие правил/нормализации.

### Для кого

| Роль | Эффект |
|------|--------|
| **Преподаватель** | Создаёт ученика логином без выдуманного `@…`; видит «логин» в списках/карточке/диалогах |
| **Ученик** | Входит по тому же логину (+ временный пароль от учителя) |

### User stories + acceptance

| ID | Story | Acceptance |
|----|--------|------------|
| US-LI-1 | Как преподаватель, хочу создать ученика с логином без `@` | `POST /api/students` с `"email": "ivanov"` → 201; в списке виден `ivanov` |
| US-LI-2 | Как преподаватель, хочу создать ученика с email-подобным логином | `"masha@school.ru"` → 201 |
| US-LI-3 | Как система, отклоняю кириллицу и мусор | `"маша"`, `"a b"`, пустая/короткая строка → 422 |
| US-LI-4 | Как пользователь, вхожу без учёта регистра | Создан `Ivanov`; login `ivanov` / `IVANOV` → успех |
| US-LI-5 | Как UI, везде говорю «логин» | Нет user-facing «Email» на login, create student, списках, drawer, confirm-диалогах, ошибках этих экранов |
| US-LI-6 | Как преподаватель, вижу hint про латиницу | Под полем логина в «Новый ученик» есть hint |
| US-LI-7 | Коллизия логина | Повтор active того же логина (case-insensitive) → 409 + русский текст про логин |

---

## 2. Tech Stack

| Слой | Стек |
|------|------|
| Backend | FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2, pytest |
| Frontend | Next.js App Router, Vitest, Playwright e2e helpers |
| Auth | httpOnly cookies, `credentials: 'include'` |
| DB | PostgreSQL / существующий app DB; колонка `users.email` без rename |

Новых внешних зависимостей **не требуется**.

---

## 3. Commands

```bash
# Backend
cd backend
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest tests/test_students.py tests/test_auth.py -q
pytest tests/multi_teacher/ -q
ruff check .
alembic upgrade head
alembic revision -m "normalize_user_email_lowercase"

# Frontend
cd frontend
npm run dev
npm run test -- CreateStudentForm LoginForm StudentList StudentCardDrawer
npm run lint
npm run build
```

---

## 4. Project Structure (затрагиваемое)

```
backend/
  app/
    schemas/students.py      # StudentCreate: pattern / validator, max 64, normalize
    schemas/auth.py          # LoginRequest: normalize lower; docs as login
    services/student_service.py
    services/auth_service.py # authenticate(login) → get_by_email(lower)
    repositories/app/user_repo.py  # get_by_email expects already-normalized
  alembic/versions/          # data migration lower(email)
  tests/test_students.py
  tests/test_auth.py

frontend/
  components/students/CreateStudentForm.tsx (+ test)
  components/auth/LoginForm.tsx (+ test)
  components/students/StudentList.tsx
  components/students/StudentCardDrawer.tsx
  components/students/GroupsPanel.tsx      # если показывает email
  components/homework/*                    # student_email labels → «логин» где user-facing
  lib/api/students.ts                      # поле payload остаётся email
  e2e/helpers/auth.ts                      # getByLabel('Логин')

docs/
  specs/student-login-identifier.md        # этот файл
  ideas/student-login-identifier.md
```

---

## 5. Code Style

Router → Service → Repository. Нормализация и валидация формата — на границе schema/service, не в UI.

```python
import re
from pydantic import BaseModel, Field, field_validator

LOGIN_RE = re.compile(r"^[a-z0-9._@+-]{3,64}$")  # после lower

class StudentCreate(BaseModel):
    email: str = Field(min_length=3, max_length=64, description="Login (stored in users.email)")
    password: str = Field(min_length=4, max_length=128)  # MIN_PASSWORD_LENGTH
    track: ExamTrack

    @field_validator("email")
    @classmethod
    def normalize_login(cls, v: str) -> str:
        login = v.strip().lower()
        if not LOGIN_RE.fullmatch(login):
            raise ValueError(
                "Login must be 3–64 chars: latin letters, digits, . _ @ + -"
            )
        return login
```

```typescript
// CreateStudentForm — type="text", label «Логин»
<label htmlFor="student-login">Логин</label>
<input id="student-login" name="email" type="text" autoComplete="username" required />
<p className="text-xs text-zinc-500">Только латиница, например ivanov</p>
```

Имя поля в JSON/`name="email"` сохраняем для совместимости API; a11y-label и видимый текст — «Логин».

---

## 6. Domain & behavior

### 6.1 Хранение

| Слой | Имя | Смысл |
|------|-----|--------|
| DB `users.email` | без rename | Уникальный идентификатор входа (lower) |
| API request/response | `email` | То же значение; в OpenAPI description — login |
| UI | «Логин» | User-facing |

### 6.2 Create / revive

1. Принять `email` из body → `strip().lower()` + regex.
2. `get_by_email(normalized)`.
3. Если active существует → 409 `"Login already registered"`.
4. Если inactive (revive per teacher-cabinet) → revive + new password.
5. Иначе создать User с `email=normalized`.

### 6.3 Authenticate

1. `login_id = payload.email.strip().lower()`.
2. `get_by_email(login_id)` + проверка пароля / `is_active`.
3. Неверный логин/пароль → 401 с detail в духе `"Invalid login or password"`; UI: «Неверный логин или пароль».

### 6.4 Что не меняем

- Пароль, роли, cookies, rate limit login.
- Soft-delete / revive семантика (кроме сравнения по lower login).
- Leaderboard `display_name` (уже не email).

---

## 7. API surface (изменения контракта текстов/валидации)

| Method | Path | Change |
|--------|------|--------|
| POST | `/api/auth/login` | Normalize input; detail/UI «login»; field name `email` остаётся |
| POST | `/api/students` | Validate+normalize login; 409 detail про login |
| GET | `/api/students` и связанные | Значение то же; UI label «логин» |
| * | responses с `email` / `student_email` | JSON keys без rename; UI copy → логин |

Breaking для клиентов: ужесточение max_length 64 и charset (ранее могли принять более длинные/unicode строки). Существующие prod-логины — email ASCII → ок после lower migration.

---

## 8. UI copy map (обязательный)

| Место | Было (ориентир) | Стало |
|-------|-----------------|--------|
| LoginForm label | Email | Логин |
| LoginForm error | Неверный email или пароль | Неверный логин или пароль |
| CreateStudentForm label | Email | Логин |
| CreateStudentForm hint | — | Только латиница, например `ivanov` |
| CreateStudentForm 409 | Этот email уже… | Этот логин уже занят. |
| CreateStudentForm 422 | Проверьте email… | Проверьте логин (латиница, 3–64), пароль (мин. 4)… |
| StudentList secondary | (email value) | тот же value; не подписывать «email» |
| StudentCardDrawer | показывать email; confirm «…для ${email}» | «логин» в текстах confirm |
| E2E `getByLabel` | Email | Логин |
| Homework list `student_email` | если есть label Email | Логин / без слова email |

Полный grep по frontend на user-facing «Email»/«email» в student/auth flows — часть задач.

---

## 9. Testing Strategy

| Уровень | Где | Что |
|---------|-----|-----|
| Unit / API | `tests/test_students.py` | create `ivanov`, `a@b.co`; 422 кириллица; 409 case-insensitive |
| Unit / API | `tests/test_auth.py` | login case-insensitive; 401 текст |
| Frontend | vitest CreateStudentForm, LoginForm, StudentCardDrawer | labels, ошибки, payload `email: "ivanov"` |
| Isolation | `tests/multi_teacher/` | без регрессий IDOR |
| Manual / e2e | auth helper label Логин | smoke login |

Coverage: новые ветки валидации + normalize обязательны; полный % не цель.

---

## 10. Boundaries

**Always:**
- Тесты на create/login до merge
- Нормализация на backend (не доверять только UI)
- IDOR / teacher scope не ослаблять
- Обновлять e2e labels вместе с UI

**Ask first:**
- Rename колонки/JSON `email` → `login`
- Менять длину 64 / charset после approve spec
- Добавлять отдельное поле display name / ФИО

**Never:**
- Кириллица в логине «на потом разрешим» без обновления spec
- Self-service email recovery в этом MVP
- Синтетические суффиксы `@local`
- Коммит секретов / `.env`

---

## 11. Success Criteria

- [ ] Учитель создаёт ученика с логином `ivanov` (без `@`) → 201, видит в списке
- [ ] Учитель создаёт `masha@school.ru` → 201
- [ ] Кириллический логин → 422
- [ ] Вход `Ivanov` / `ivanov` работает после create
- [ ] На экранах login + students (+ drawer/confirms) нет user-facing «Email»
- [ ] Hint под полем логина в форме создания
- [ ] Alembic: существующие `users.email` в lower-case
- [ ] `pytest` (students + auth) и затронутые vitest зелёные
- [ ] API JSON keys `email` / `student_email` не переименованы

---

## 12. Out of scope (Not Doing)

- Отдельная колонка `login` / `username`
- Rename API/DB `email` → `login`
- Display name / ФИО ученика
- Invite-коды, SSO, автогенерация логинов
- Self-service восстановление пароля
- Изменение teacher provisioning CLI (кроме совместимости lower при login)

---

## 13. Open Questions

*(пусто после assumptions — спорные пункты вынесены в §Assumptions)*

Если нужен другой max_length или запрет `@` — править assumptions **до** PLAN.

---

## 14. Decisions log

| Решение | Выбор | Источник |
|---------|--------|----------|
| Направление | A — reuse `users.email` | idea-refine |
| UI | Везде «логин» | user |
| Алфавит | Латиница only | user |
| `@` | Разрешён | user |
| Normalize | `lower()` save + login | user |
| Мин. пароль (set) | 4 символа (ученик + teacher seed) | user |
| Max length MVP | 64 | assumption 2 |
| Hint | Да | assumption 7 |
| Data migration lower | Да | assumption 6 |
