**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T005 — Исправить PROJECT_SLUG (leading dash) и conn.commit() в cmd_query

## Customer-facing инкремент

После исправлений `/archive-session` будет находить JSONL-файл текущей сессии без ручных workaround-ов. `python3 session_archive.py query "UPDATE ..."` будет реально сохранять изменения в SQLite.

---

## Баги

### BUG-PROJECT-SLUG-MISMATCH (BUG-42 / BUG-04 / BUG-20 / BUG-SLUG-LEADING-DASH)

**Симптом:** `/archive-session` не находит JSONL-файл, уходит в fallback или захватывает JSONL из другого проекта. Каждый раз требуется ручной поиск директории.

**Root cause:** В `archive-session.md` (строка 28) slug вычисляется как:
```bash
PROJECT_SLUG=$(echo "$PWD" | sed 's|^/||; s|/|-|g')
```
Для пути `/Users/is/personal/Projects/cleaning-bot` это даёт `Users-is-personal-Projects-cleaning-bot` (без ведущего дефиса). Реальная директория в `~/.claude/projects/` называется `-Users-is-personal-Projects-cleaning-bot` (ведущий `/` тоже становится `-`).

Команда `s|^/||` отбрасывает ведущий `/` вместо того чтобы заменить его на `-`.

**Повторялось:** 6+ раз (BUG-04, BUG-20, BUG-42, BUG-PROJECT-SLUG-MISMATCH — один и тот же баг).

**Fix:**
В файле `/Users/is/.claude/commands/archive-session.md`, строка 28 — заменить:
```bash
PROJECT_SLUG=$(echo "$PWD" | sed 's|^/||; s|/|-|g')
```
на:
```bash
PROJECT_SLUG=$(echo "$PWD" | sed 's|/|-|g')
```

Убрав `s|^/||`, ведущий `/` преобразуется в `-` вместе со всеми остальными слешами. Результат: `-Users-is-personal-Projects-cleaning-bot` — точное совпадение с именем директории в `~/.claude/projects/`.

---

### BUG-QUERY-NO-COMMIT — DML через `query` субкоманду не сохраняется

**Симптом:** `python3 session_archive.py query "UPDATE sessions SET ai_model='claude-sonnet-4-6' WHERE id='xxx'"` завершается без ошибок, но изменения не сохраняются в SQLite. Приходится использовать `python3 -c "import sqlite3; ..."` напрямую.

**Root cause:** `cmd_query()` (`session_archive.py:1632`) не вызывает `conn.commit()`:
```python
def cmd_query(sql):
    conn = get_db()
    rows = conn.execute(sql).fetchall()
    print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    conn.close()  # ← commit не был вызван, транзакция откатывается
```

SQLite в Python по умолчанию работает в режиме автоматических транзакций. Без явного `commit()` DML-операции (INSERT/UPDATE/DELETE) откатываются при закрытии соединения.

**Повторялось:** 1 раз зафиксировано, но баг присутствует с первой версии кода.

**Fix:**
В `session_archive.py:1632-1636` добавить `conn.commit()` перед `conn.close()`:
```python
def cmd_query(sql):
    conn = get_db()
    rows = conn.execute(sql).fetchall()
    print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    conn.commit()  # ← добавить
    conn.close()
```

---

## Scope

- Исправить `sed` в `/Users/is/.claude/commands/archive-session.md:28`
- Добавить `conn.commit()` в `session_archive.py:cmd_query()`

## Out of scope

- Ретроспективные исправления сессий с неверным slug
- Изменения логики fallback-поиска JSONL

---

## Как протестировать

1. **Slug fix:** Запустить `/archive-session` в любом проекте → убедиться что `JSONL_DIR` найден без fallback-а
2. **Query fix:**
   ```bash
   python3 session_archive.py query "SELECT id FROM sessions LIMIT 1"
   # запомнить ID
   python3 session_archive.py query "UPDATE sessions SET open_issues='test' WHERE id='<ID>'"
   python3 session_archive.py query "SELECT open_issues FROM sessions WHERE id='<ID>'"
   # должно вернуть 'test', а не пустую строку
   ```

## Критерии приёмки

1. `/archive-session` находит JSONL без fallback-а во всех 3 тестовых проектах (cleaning-bot, sproektirui, SessionArchive)
2. `session_archive.py query "UPDATE ..."` сохраняет изменения — подтверждается последующим SELECT
