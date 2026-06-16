# Security Checklist

Краткий справочник для веб-приложений. Используй с `security-and-hardening`.

## Threat Modeling (начни здесь)

- [ ] Границы доверия (HTTP, uploads, webhooks, внешние API)
- [ ] Активы (credentials, PII, admin)
- [ ] STRIDE по границам
- [ ] Abuse cases рядом с use cases

## Pre-Commit

- [ ] Нет секретов: `git diff --staged | findstr /i "password secret api_key token"`
- [ ] `.gitignore`: `.env`, `.venv`, `*.pem`, `*.key`
- [ ] `.env.example` с плейсхолдерами

## Authentication

- [ ] Пароли: bcrypt (≥12 rounds) / argon2
- [ ] JWT: короткий access, refresh rotation (если используется)
- [ ] Rate limit login (≤10 / 15 мин)
- [ ] Reset tokens: TTL ≤1ч, single-use

## Authorization

- [ ] Каждый protected endpoint — auth
- [ ] Проверка ownership/role (IDOR)
- [ ] Admin endpoints — role check

## Input Validation

- [ ] Pydantic на границах API
- [ ] Allowlists, не denylists
- [ ] Ограничения длины строк
- [ ] SQLAlchemy parameterized — нет f-string SQL
- [ ] File upload: type, size, content check
- [ ] SSRF: allowlist URL, block private IP

## Security Headers

Настрой через reverse proxy или middleware:
```
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```

## CORS (FastAPI)

```python
# Хорошо
allow_origins=["https://yourdomain.com"]

# НИКОГДА в production:
allow_origins=["*"]  # с credentials
```

## Data Protection

- [ ] `password_hash` не в response
- [ ] Секреты не в логах
- [ ] HTTPS
- [ ] Encrypted backups (если требуется)

## Dependencies (Python)

```bash
pip audit
# или
safety check -r requirements.txt
```

- [ ] Lockfile в git (`requirements.txt` / `poetry.lock`)
- [ ] CI: `pip install -r requirements.txt` (pinned versions)
- [ ] Новые пакеты — review перед добавлением

## Error Handling

```python
# Production
raise HTTPException(500, detail="Internal server error")

# НИКОГДА клиенту:
# str(exc), traceback, SQL query
```

## OWASP Top 10 (кратко)

| # | Уязвимость | Prevention |
|---|------------|------------|
| 1 | Broken Access Control | Authz на каждом endpoint |
| 2 | Cryptographic Failures | HTTPS, strong hashing |
| 3 | Injection | Parameterized queries, Pydantic |
| 4 | Insecure Design | Threat model, spec-driven |
| 5 | Security Misconfiguration | Headers, minimal permissions |
| 6 | Vulnerable Components | pip audit |
| 7 | Auth Failures | Rate limit, session/JWT |
| 8 | Data Integrity | Signed artifacts, lockfile |
| 9 | Logging Failures | Security events, не секреты |
| 10 | SSRF | Allowlist URLs |

## AI/LLM (если есть)

- [ ] Output модели = untrusted
- [ ] Permissions в коде
- [ ] Секреты вне prompt
- [ ] Scoped tools, confirm destructive actions
- [ ] Token/rate/depth limits
