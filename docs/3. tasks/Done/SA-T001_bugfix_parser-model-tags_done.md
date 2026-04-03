**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T001 — Исправить парсинг модели и мусорных тегов

## Customer-facing инкремент

После архивирования сессии `ai_model` в БД и тегах содержит корректное название модели (`claude-sonnet-4-6`), а теги `skill:` не содержат XML-тегов и компонентов путей из system-reminder.

---

## Баги

### BUG-34 — модель всегда `claude` вместо конкретного ID

**Симптом:** `sessions.ai_model = 'claude'`, тег `model: claude`, заголовок MD — везде `claude` вместо `claude-sonnet-4-6`.

**Root cause:** `parse_claude_jsonl()` инициализирует `model = None` и не читает поле из JSONL-записей. В Claude JSONL модель присутствует в записях с `role = assistant` — в поле `message.model` или верхнеуровневом `model`.

**Повторялось:** 18+ раз подряд, каждый раз исправляется вручную в SQLite.

**Fix:** Добавить в цикл парсинга извлечение модели:
```python
# внутри цикла parse_claude_jsonl(), при role == "assistant"
if role == "assistant" and not model:
    model = msg.get("model") or entry.get("model")
```

---

### BUG-TAGS-XML — мусорные теги из XML-тегов и system-reminder

**Симптом:** В `session_tags` с категорией `skill` попадают:
- XML-имена тегов: `command-message`, `command-name`, `task-id`, `task-notification`, `subagents`, `tmp`
- Компоненты путей и опций из system-reminder: `dev`, `etc`, `home`, `hooks`, `json`, `path`, `projects`, `rename`, `opt`, `memory`, `localhost`

**Root cause:** `detect_skills_used()` применяет regex `(?<!\w)/([a-z][a-z0-9-]+)` ко всему тексту сообщений, включая system-reminder с путями вида `/Users/is/...`, `/path/to/...` и XML-атрибутами. Плюс `<command-name>` regex захватывает содержимое тегов включая системные.

**Повторялось:** Каждая сессия. Вручную удаляется 10–20 фантомных тегов.

**Fix:**
1. Применять `/skill` regex **только к user-сообщениям**, и только к строкам начинающимся с `/` (slash-команды), а не к середине любого текста.
2. Добавить blocklist известных ложных значений: `{'command-message', 'command-name', 'task-id', 'task-notification', 'subagents', 'localhost', 'dev', 'etc', 'home', 'hooks', 'json', 'path', 'projects', 'rename', 'opt', 'memory', 'tmp', 'private', 'status', 'summary', 'output-file', 'command-args'}`.
3. Ограничить длину найденного skill: пропускать значения длиннее 30 символов.

---

## Scope

- Фикс `parse_claude_jsonl()` — читать `model` из JSONL-записей
- Фикс `detect_skills_used()` — убрать мусорные теги (blocklist + сужение regex)
- Проверить что существующие сессии в БД не ломаются (новые архивирования будут корректными; старые — не трогаем)

## Out of scope

- Исправление уже записанных данных в БД (ручные правки прошлых сессий остаются как есть)
- Другие баги парсера (BUG-ARTIFACTS-WRONG, BUG-PROJECT-SLUG-MISMATCH и пр.)
- Добавление тестов (отдельная задача)

---

## Как протестировать

1. Запустить `/archive-session` в любом Claude-проекте
2. Проверить: `python3 session_archive.py query "SELECT ai_model FROM sessions ORDER BY created_at DESC LIMIT 1"`
3. Проверить теги: `python3 session_archive.py query "SELECT value FROM session_tags WHERE category='skill' AND session_id=(SELECT id FROM sessions ORDER BY created_at DESC LIMIT 1)"`
4. Убедиться что нет `command-message`, `command-name`, `dev`, `tmp` и подобных в списке

## Критерии приёмки

1. `sessions.ai_model` содержит `claude-sonnet-4-6` (или другой конкретный ID, не `claude`)
2. Тег `model: claude-sonnet-4-6` в `session_tags`
3. В тегах `skill:` нет XML-тегов и компонентов путей из blocklist
4. Реально использованные навыки (`/archive-session`, `/intro`, `/fix` и т.д.) присутствуют в тегах
