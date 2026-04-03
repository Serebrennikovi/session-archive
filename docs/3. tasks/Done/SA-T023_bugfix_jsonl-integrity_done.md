**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T023 — Исправить выбор JSONL и уникальность в SQLite

## Customer-facing инкремент

После архивирования сессии запись гарантированно соответствует правильному JSONL-файлу (не перепутается с соседней сессией), а повторная архивация не создаёт дублирующих тегов/задач.

---

## Баги

### BUG-WRONG-JSONL / BUG-JSONL-MTIME — неправильный JSONL выбирается из-за mtime tie-break

**Симптом:** `archive-current` захватывает JSONL соседней сессии вместо текущей. В сессии `713c9e3e` захватился `21d573f9` (T143, 1.5MB) вместо `713c9e3e` (T144, 842KB) — оба имели одинаковый mtime с точностью до минуты. Summary T143-сессии оказался перезаписан.

В сессии `eb2f67de`: `ls -t | head -1` вернул `d3cec0d7` (4 сообщения) вместо `eb2f67de` (27 сообщений) — mtime не синхронен.

**Root cause:** `find_current_jsonl()` использует `ls -t` с точностью до минуты. При tie-break в пределах одной минуты выбирается произвольный или более крупный файл.

**Повторялось:** 2+ раза, каждый раз исправляется вручную.

**Fix:**
```python
# Вместо ls -t использовать Python os.path.getmtime() с float-точностью
import os, glob

def find_current_jsonl(project_dir):
    files = glob.glob(os.path.join(project_dir, '*.jsonl'))
    if not files:
        return None
    # Сортировать по float mtime (наносекундная точность)
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    # Если два файла с mtime разницей < 60 сек — брать файл с наибольшим числом строк
    if len(files) >= 2:
        t1 = os.path.getmtime(files[0])
        t2 = os.path.getmtime(files[1])
        if abs(t1 - t2) < 60:
            # tie-break по размеру файла (больший файл = больше сообщений)
            files[:2] = sorted(files[:2], key=lambda f: os.path.getsize(f), reverse=True)
    return files[0]
```

---

### BUG-SQLITE-NO-UNIQUE-CONSTRAINT — дубли тегов/задач при повторной архивации

**Симптом:** `session_tags` и `session_tasks` не имеют UNIQUE constraint на `(session_id, category, value)` / `(session_id, task_id)`. При `INSERT OR IGNORE` без UNIQUE constraint вставляются дубли. В сессии `aa723310` пришлось делать полный DELETE + re-INSERT вместо incremental update.

**Root cause:** Таблицы созданы без UNIQUE constraints, что делает `INSERT OR IGNORE` бесполезным.

**Повторялось:** 1+ раз, обходной путь: DELETE + reinsert.

**Fix:**
```sql
-- Migration: добавить UNIQUE constraints
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_tags_unique
    ON session_tags(session_id, category, value);

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_tasks_unique
    ON session_tasks(session_id, task_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_events_unique
    ON session_events(session_id, event_type);

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_artifacts_unique
    ON session_artifacts(session_id, file_path, action);
```

В `_ensure_schema()` добавить создание этих индексов. После этого `INSERT OR IGNORE` будет работать корректно для incremental updates.

---

### BUG-ARCHIVE-OVERWRITE (новый вариант) — повторный запуск перезаписывает теги

**Симптом:** Когда `archive-current` вызывается дважды на одном JSONL (или после дополнительных действий), второй вызов перезаписывает теги и задачи без сохранения ручных правок. В сессии `aa723310` явно переданный `--summary` при первом вызове потерялся при втором.

**Root cause:** Повторный вызов делает DELETE + INSERT для session_tags/session_tasks без проверки, были ли они скорректированы вручную.

**Повторялось:** 1+ раз.

**Fix:**
```python
# Добавить флаг --keep-tags и --keep-tasks в archive-current
# При повторной архивации с тем же session_id:
# - обновлять только msg_count, tool_call_count, last_updated
# - НЕ трогать summary если уже есть sessions.summary_manual = 1
# - НЕ пересобирать теги/задачи если уже есть --keep-tags флаг
# Добавить проверку:
if existing_session and existing_session.get('summary_manual'):
    skip_summary_update = True
```

---

## Scope

- Заменить `ls -t` / shell-based mtime на Python `os.path.getmtime()` в `find_current_jsonl()`
- Добавить tie-break по размеру файла при mtime разнице < 60 сек
- Добавить UNIQUE indexes в `_ensure_schema()` для session_tags, session_tasks, session_events, session_artifacts
- Добавить флаг `--keep-tags` / `--keep-tasks` для защиты от перезаписи при повторной архивации

## Out of scope

- Полный рефактор find_current_jsonl (только precision fix)
- Изменение формата SQLite-схемы (только добавление индексов)

---

## Как протестировать

1. Создать два JSONL в `~/.claude/projects/test/` с одинаковым mtime (touch -t)
2. Запустить `archive-current` → убедиться что выбирается файл с большим числом строк
3. Запустить `archive-current` дважды → убедиться что session_tags не содержит дублей

## Критерии приёмки

1. При mtime tie-break выбирается JSONL с большим числом строк, не произвольный
2. `session_tags` с UNIQUE index: второй `INSERT OR IGNORE` с теми же (session_id, category, value) не создаёт дубль
3. `archive-current` с `--keep-tags` не перезаписывает ручные правки тегов
