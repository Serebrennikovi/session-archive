**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T011 — Исправить целостность повторной архивации (archive overwrite + wrong session)

## Customer-facing инкремент

После архивирования сессии повторный запуск `/archive-session` или `/verify-archive` не затрёт правильный summary, не подтянет чужой JSONL и не перезапишет diff данными другой сессии. Ручные правки `sessions.summary` сохраняются при re-archive.

---

## Баги

### BUG-ARCHIVE-OVERWRITE — повторный archive перезаписывает правильный summary

**Симптом:** `archive-current` запускается дважды (или `/verify-archive` вызывает его повторно). Второй запуск перезаписывает `sessions.summary` и `msg_count` автогенерированным значением, даже если первый запуск был с явным `--summary`. Вручную заданный summary теряется.

**Root cause:** `archive-current` при повторном вызове на том же `session_id` всегда перезаписывает `summary`, `msg_count`, `tool_call_count` — нет проверки на наличие уже сохранённого `summary_manual`.

**Повторялось:** 5+ раз, каждый раз summary восстанавливается вручную.

**Fix:**
```python
# В archive-current: при UPDATE сессии проверять наличие ручного summary
def upsert_session(conn, session_id, data):
    existing = conn.execute(
        "SELECT summary_manual FROM sessions WHERE session_id=?", (session_id,)
    ).fetchone()

    if existing and existing['summary_manual']:
        # Не перезаписываем summary если был задан вручную
        data.pop('summary', None)

    # Обновляем только msg_count, tool_call_count и незащищённые поля
    conn.execute("UPDATE sessions SET ... WHERE session_id=?", ...)
```

Добавить колонку `summary_manual TEXT` в `sessions`. При явном `--summary` писать в `summary_manual`. При автогенерации — только в `summary`. При экспорте: `COALESCE(summary_manual, summary)`.

---

### BUG-SUMMARY-REGENERATE — verify-archive перегенерирует и перезаписывает summary

**Симптом:** После `/archive-session` + ручного исправления summary, запуск `/verify-archive` вызывает повторную архивацию без `--summary`. Автогенерированный summary («Код-ревью T02_s01_auth») перезаписывает правильный («Повторное code review T01»).

**Root cause:** `/verify-archive` скилл вызывает `archive-current` без `--summary` флага, не проверяя есть ли уже сохранённый summary в SQLite.

**Повторялось:** 3+ раза.

**Fix:**
- Тот же `summary_manual` guard из BUG-ARCHIVE-OVERWRITE.
- В `/verify-archive` скилле: перед вызовом `archive-current` проверять `SELECT summary FROM sessions WHERE session_id=?`; если есть — передавать `--summary` явно, или вообще не перезаписывать.

---

### BUG-DIFF-WRONG-SESSION — дифы из другой сессии попадают в экспорт

**Симптом:** Секция `## Diffs` в экспорте содержит изменения из ПРЕДЫДУЩЕЙ сессии (например, `html.escape` в `contact.py` из T02-ревью), хотя текущая сессия — T01. При `re-archive` без `--jsonl` использовался другой JSONL-файл по mtime.

**Root cause:** `find_current_jsonl()` выбирает файл по `mtime` без секундной точности (`ls -t` даёт минутный тай-брейк). При tie-break побеждает больший по размеру файл — другой сессии.

**Повторялось:** 4+ раза.

**Fix:**
```python
def find_current_jsonl(project_dir):
    jsonl_files = list(Path(project_dir).glob("*.jsonl"))
    if not jsonl_files:
        return None
    # Использовать float mtime для секундной точности
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)
```

Дополнительно: при `archive-current` сравнивать `session_id` в JSONL с существующим `session_id` в SQLite — если не совпадает, предупреждать и не перезаписывать.

```python
def validate_jsonl_session(conn, jsonl_path, expected_session_id):
    actual_id = extract_session_id(jsonl_path)
    existing = conn.execute(
        "SELECT session_id FROM sessions WHERE session_id=?", (actual_id,)
    ).fetchone()
    if existing and actual_id != expected_session_id:
        raise ValueError(f"JSONL session_id {actual_id} != expected {expected_session_id}")
```

---

## Scope

- Добавить колонку `summary_manual` в `sessions` (миграция)
- При `--summary` флаге писать в `summary_manual`
- При re-archive: не перезаписывать `summary` если `summary_manual` не пуст
- В `find_current_jsonl()`: использовать `f.stat().st_mtime` (float) вместо `ls -t`
- При re-archive: проверять совпадение `session_id` из JSONL с ожидаемым

## Out of scope

- Полная история версий summary
- Автогенерация summary из JSONL-транскрипта (отдельная задача)

---

## Как протестировать

1. Запустить `/archive-session` с явным summary → проверить `sessions.summary_manual`
2. Запустить `/verify-archive` повторно → summary не должен изменится
3. Создать два JSONL с одинаковым `mtime` (минута) → `find_current_jsonl()` должен взять правильный по float mtime
4. Попытаться сделать `archive-current` с JSONL чужой сессии → должно быть предупреждение

## Критерии приёмки

1. Повторный `archive-current` без `--summary` не перезаписывает `summary_manual`
2. `find_current_jsonl()` использует `st_mtime` с секундной точностью
3. При несовпадении `session_id` в JSONL — предупреждение в stderr, данные не перезаписываются
4. Экспорт MD использует `summary_manual` если он задан
