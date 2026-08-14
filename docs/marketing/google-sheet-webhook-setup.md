# Google Sheet webhook для заявок (Leads)

Инструкция для владельца: настроить CRM-таблицу и Apps Script, чтобы `POST /api/leads` из chim_web добавлял строки автоматически.

**Связано:** [`leads-tracker-template.csv`](./leads-tracker-template.csv), spec [`docs/specs/seo-marketing-site-nextjs.md`](../specs/seo-marketing-site-nextjs.md) §6.

---

## 1. Создать Google Sheet

1. Откройте [Google Sheets](https://sheets.google.com) → **Создать** → пустая таблица.
2. Назовите файл, например: **Leads himych**.
3. В первой строке (заголовки) вставьте колонки из шаблона:

```text
date | name | contact | class | exam | source | utm_source | utm_campaign | trial_date | paid | bundle | notes
```

Или импортируйте CSV: **Файл → Импорт → Загрузить** → [`leads-tracker-template.csv`](./leads-tracker-template.csv).

Колонки `trial_date`, `paid`, `bundle` оставьте пустыми — их заполняете вы вручную после звонка.

---

## 2. Apps Script: `doPost`

1. В таблице: **Расширения → Apps Script**.
2. Удалите содержимое `Code.gs` и вставьте:

```javascript
/**
 * Web App endpoint for chim_web POST /api/leads
 * Expects JSON body from LeadService (see backend/app/services/lead_service.py)
 */
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var body = JSON.parse(e.postData.contents);

    sheet.appendRow([
      body.date || new Date().toISOString(),
      body.name || "",
      body.contact || "",
      body.class || "",
      body.exam || "",
      body.source || "",
      body.utm_source || "",
      body.utm_campaign || "",
      "", // trial_date — владелец
      "", // paid
      "", // bundle
      body.notes || "",
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
```

3. **Сохранить** (Ctrl+S). Проект можно назвать `himych-leads-webhook`.

---

## 3. Deploy Web App

1. **Развернуть → Новое развертывание**.
2. Тип: **Веб-приложение**.
3. **Выполнять от имени:** Me (ваш аккаунт).
4. **У кого есть доступ:** **Anyone** (Anyone with the link — для MVP; URL держите в `.env`, не публикуйте).
5. **Развернуть** → скопируйте **URL веб-приложения** (вид `https://script.google.com/macros/s/.../exec`).

---

## 4. Прописать URL в chim_web

**Локально** (`backend/.env` или корневой `.env` для Docker):

```bash
GOOGLE_SHEETS_WEBHOOK_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

**Docker Compose:** та же переменная в корневом `.env` (прокидывается в `backend` — см. `docker-compose.yml`).

Перезапустите backend после изменения env.

---

## 5. Проверка

### curl (ручной тест webhook)

```bash
curl -X POST "$GOOGLE_SHEETS_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-07-29T12:00:00+00:00",
    "name": "Тест",
    "contact": "+79001234567",
    "class": "11",
    "exam": "ЕГЭ",
    "source": "/zapis",
    "utm_source": "manual",
    "utm_campaign": "test",
    "notes": "curl smoke test"
  }'
```

Ожидание: новая строка в Sheet, ответ `{"ok":true}`.

### Через API chim_web

```bash
curl -X POST http://localhost:8080/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тест API",
    "phone": "+79001234567",
    "school_class": "11",
    "goal": "ege",
    "source_page": "/zapis",
    "utm_source": "vk",
    "utm_campaign": "aug2026_diag"
  }'
```

Ожидание: `201` + `{"id":"...","status":"accepted"}` + строка в Sheet.

### С телефона

Откройте `/zapis` на staging (IP или домен), отправьте форму — проверьте строку и UTM в Sheet.

---

## 6. Безопасность и эксплуатация

| Риск | Митигация |
|------|-----------|
| URL утёк | Развернуть новую версию Web App → обновить `.env` |
| Спам | Rate limit 5/min на `/api/leads` (slowapi) |
| Sheet недоступен | Backend всё равно отвечает **201** и пишет `lead_webhook_failed` в лог — проверяйте логи VPS ежедневно в августе |

**Не коммитьте** webhook URL в git — только в `.env` на сервере.

---

## 7. Troubleshooting

| Симптом | Решение |
|---------|---------|
| 401/403 от Google | Deploy с доступом **Anyone**; авторизуйте скрипт при первом запуске |
| Пустые строки | Проверьте `Content-Type: application/json` и имена полей в `doPost` |
| 201, но нет строки | Смотрите backend-лог: `lead_webhook_failed`; проверьте URL и квоты Google |
| Дубликаты при тестах | Нормально; удалите тестовые строки вручную |

---

**Готово:** после 5 тестовых сабмитов с телефона (Slice 0 checkpoint) можно включать VK Ads на `/zapis?utm_*`.
