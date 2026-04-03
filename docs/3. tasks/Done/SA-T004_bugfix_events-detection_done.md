**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T004 — Исправить детекцию событий (phantom events + missing session_archived)

## Customer-facing инкремент

После архивирования сессии секция `Events` будет отражать реально произошедшие события (задеплоили, запустили тесты, сделали коммит), а не слова из диалога. `session_archived` будет присутствовать всегда.

---

## Баги

### BUG-31 / BUG-EVENTS-FALSE-POSITIVE — Phantom events из regex по тексту

**Симптом:** Events содержат `handoff_read`, `changelog_read`, `deploy`, `review_done`, `task_completed` хотя соответствующих tool calls в сессии не было. Например, простое упоминание слова "done" в диалоге даёт `task_completed`.

**Root cause:** `detect_events()` (`session_archive.py:558`) сканирует весь конкатенированный текст сообщений regex-паттернами:
```python
text = " ".join(m["text"] for m in messages).lower()
checks = [
    ("handoff_read",   r'handoff'),
    ("changelog_read", r'changelog'),
    ("review_done",    r'code review|codereview|ревью'),
    ("task_completed", r'completed|done|завершена'),
    ...
]
```
Любое упоминание слова в prose триггерит событие.

**Повторялось:** 25+ раз, каждый раз исправляется вручную.

**Fix:**
Заменить text-matching на проверку по фактическим tool calls из `artifacts`:

```python
def detect_events(messages, artifacts):
    events = []
    seen = set()

    def add(event_type):
        if event_type not in seen:
            seen.add(event_type)
            events.append({"event_type": event_type, "detail": None})

    # Read-based events: только если файл реально читался через Read tool
    read_paths = {a["path"].lower() for a in artifacts if a.get("action") == "read"}
    for path in read_paths:
        if "handoff" in path:
            add("handoff_read")
        if "changelog" in path:
            add("changelog_read")
        if re.search(r'adv-s\d+|spec', path):
            add("spec_read")

    # Command-based events: из artifact action labels (уже надёжны)
    label_map = {
        "event:commit":     "commit_made",
        "event:push":       "push_made",
        "event:deploy":     "deploy",
        "event:tests":      "tests_run",
        "event:pr_created": "pr_created",
    }
    for a in artifacts:
        if a.get("action") in label_map:
            add(label_map[a["action"]])

    # deploy через Bash команды (уже детектируется в _detect_command_events)
    # — оставить как есть (event:deploy из artifacts)

    # Удалить: review_done, task_completed из text (слишком шумно)
    # Эти события должны добавляться только через явные skill-вызовы или HANDOFF-изменения
    # TODO: добавить когда будет надёжный способ детектировать Skill-вызовы

    return events
```

---

### BUG-EVENTS-MISSING — Отсутствует `session_archived`

**Симптом:** После успешного `/archive-session` событие `session_archived` не попадает в запись. Каждый раз добавляется вручную.

**Root cause:** `detect_events()` не имеет логики для `session_archived`. Само архивирование выполняется скриптом `session_archive.py`, который сам себя не фиксирует как событие.

**Повторялось:** 15+ раз.

**Fix:**
В `cmd_archive_current()` после успешной записи в БД добавить событие программно:

```python
# В конце cmd_archive_current(), после _upsert_session():
conn = get_db()
conn.execute(
    "INSERT OR IGNORE INTO session_events (session_id, event_type, detail) VALUES (?,?,?)",
    (session_id, "session_archived", None)
)
conn.commit()
conn.close()
```

Либо проще — добавить `session_archived` в список событий в `_build_metadata()` безусловно:
```python
# В конце detect_events(), перед return:
add("session_archived")  # всегда — archive-current вызывается только для завершённых сессий
```

---

## Scope

- Переписать `detect_events()`: убрать text-regex, оставить только artifact-based детекцию
- Убрать из checks: `handoff_read` (→ через read_paths), `changelog_read` (→ через read_paths), `review_done` (нет надёжного сигнала), `task_completed` (нет надёжного сигнала)
- Добавить `session_archived` безусловно
- Обновить tests (если есть) или задокументировать ожидаемое поведение

## Out of scope

- `review_done` и `task_completed` — оставить без детекции до появления Skill tool call API
- Ретроспективная правка уже записанных сессий

---

## Как протестировать

1. Запустить `/archive-session` после сессии где HANDOFF читался, но `deploy` не делался
2. Проверить в DB: `python3 session_archive.py query "SELECT event_type FROM session_events WHERE session_id='<id>'"`
3. Убедиться: `handoff_read` есть, `deploy`/`review_done`/`task_completed` — нет
4. Убедиться: `session_archived` присутствует

## Критерии приёмки

1. `handoff_read` появляется только если HANDOFF.md был в Read tool calls
2. `changelog_read` появляется только если CHANGELOG.md был в Read tool calls
3. `task_completed` и `review_done` НЕ генерируются автоматически из текста
4. `session_archived` присутствует в каждой архивированной сессии
5. Ручные правки Events в verify-archive сводятся к нулю на 3 подряд сессиях
