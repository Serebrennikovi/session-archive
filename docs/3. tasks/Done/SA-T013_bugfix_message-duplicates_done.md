**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T013 — Исправить дубли сообщений в session_messages и Transcript

## Customer-facing инкремент

После архивирования сессии `Messages` count соответствует реальному числу сообщений. Раздел `## Transcript` не содержит повторяющихся блоков. Не нужно вручную дедуплицировать сообщения и пересчитывать `msg_count`.

---

## Баги

### BUG-14 / BUG-21 — соседние дублирующиеся (role, text) в session_messages

**Симптом:** `session_messages` (SQLite) и `## Transcript` (MD-экспорт) содержат соседние дублирующиеся блоки — два подряд идентичных `(role, content)`. Из-за этого `sessions.msg_count` завышен (например, `33 -> 21`, `27 -> 17`). `user_msg_count` тоже завышен.

**Root cause:** Парсер JSONL сохраняет сообщения без дедупликации соседних идентичных пар. Возможные причины появления дублей в JSONL:
1. Один JSONL-блок парсится дважды (при re-parse после retry)
2. При streaming assistant-сообщений один блок записывается несколько раз с одинаковым content
3. `session_messages` не имеет UNIQUE constraint на `(session_id, role, position)`

**Повторялось:** 7+ раз, каждый раз дедуплицируется вручную.

**Fix:**
```python
def deduplicate_adjacent_messages(messages):
    """Удалить соседние дубли (role, text) из списка сообщений."""
    if not messages:
        return messages
    deduped = [messages[0]]
    for msg in messages[1:]:
        prev = deduped[-1]
        if msg['role'] == prev['role'] and msg['content'] == prev['content']:
            continue  # пропустить дубль
        deduped.append(msg)
    return deduped

# Применять ПЕРЕД сохранением в SQLite и перед markdown-экспортом
messages = deduplicate_adjacent_messages(raw_messages)
session['msg_count'] = len([m for m in messages if m['role'] == 'assistant'])
session['user_msg_count'] = len([m for m in messages if m['role'] == 'user'])
```

Дополнительно — добавить UNIQUE constraint в SQLite:
```sql
-- Миграция
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_messages_unique
ON session_messages(session_id, role, position);
```

Или сортировать по `position` и проверять на дубли при INSERT:
```python
conn.execute("""
    INSERT OR IGNORE INTO session_messages (session_id, role, content, position)
    VALUES (?, ?, ?, ?)
""", (session_id, role, content, position))
```

---

## Scope

- Добавить `deduplicate_adjacent_messages()` в парсер сообщений
- Применять дедупликацию до записи в SQLite и до markdown-экспорта
- Пересчитывать `msg_count` и `user_msg_count` после дедупликации
- Добавить `INSERT OR IGNORE` или UNIQUE index на `session_messages`

## Out of scope

- Дедупликация несоседних повторений (один и тот же вопрос задан дважды — это нормально)
- Изменение структуры JSONL или парсинга tool calls

---

## Как протестировать

1. Взять JSONL сессии где известны дубли (например `019d51c7`, `019d52e2`, `019d51d4`)
2. Запустить `/archive-session`
3. Проверить: `sessions.msg_count` совпадает с реальным числом уникальных сообщений
4. Проверить: `## Transcript` не содержит двух подряд идентичных блоков
5. Повторный `/archive-session` на том же JSONL → msg_count не меняется

## Критерии приёмки

1. Соседние дубли `(role, content)` не сохраняются в `session_messages`
2. `msg_count` = фактическое число уникальных assistant-сообщений
3. `user_msg_count` = фактическое число уникальных user-сообщений
4. `## Transcript` в MD-экспорте не содержит повторяющихся соседних блоков
