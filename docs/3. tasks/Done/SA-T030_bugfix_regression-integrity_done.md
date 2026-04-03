**Дата:** 2026-04-03
**Статус:** done 2026-04-03
**Спецификация:** —

# SA-T030 — Исправить регрессии: overwrite guard, msg-dedup, open_issues fmt

## Customer-facing инкремент

После архивирования сессии повторный вызов archive-current не затирает вручную выставленный summary; session_messages не содержит дублей и msg_count точный; open_issues не содержит артефактов markdown-форматирования.

---

## Баги

### BUG-ARCHIVE-OVERWRITE (regression) — повторный archive-current перезаписывает summary

**Симптом:** Если `archive-current` вызывается дважды на одном JSONL (или `/verify-archive` запускается после `/archive-session`), второй вызов перезаписывает `sessions.summary` и `sessions.msg_count`. Явно переданный `--summary` при первом вызове теряется.

**Root cause:** SA-T011 добавил `summary_manual` флаг, но защита не срабатывает во всех путях вызова. В частности, при повторной архивации с тем же session_id guard обходится, если JSONL успел дорасти (новые сообщения) или если вызов идёт без `--summary`.

**Повторялось:** 2+ раза (2026-04-03 Arbitra aa723310, 2026-04-03 cleaning-bot 09796f55 — упомянут как причина потери summary).

**Fix:**
```python
def archive_session(session_id, summary=None, keep_summary=False, ...):
    existing = conn.execute(
        "SELECT summary, summary_manual FROM sessions WHERE id=?", (session_id,)
    ).fetchone()

    if existing and existing['summary_manual'] == 1 and keep_summary:
        # Не перезаписывать summary, только обновить msg_count/tool_call_count
        conn.execute(
            "UPDATE sessions SET msg_count=?, tool_call_count=? WHERE id=?",
            (msg_count, tool_count, session_id)
        )
    else:
        # Обычная логика
        if summary:
            conn.execute(
                "UPDATE sessions SET summary=?, summary_manual=1 WHERE id=?",
                (summary, session_id)
            )
        else:
            conn.execute(
                "UPDATE sessions SET msg_count=?, tool_call_count=? WHERE id=?",
                (msg_count, tool_count, session_id)
            )
```

Добавить флаг `--keep-summary` в CLI `archive-current`. При повторном вызове без `--summary` — НЕ трогать summary, только обновлять метрики.

---

### BUG-MSG-DEDUP-REGRESSION — дубли сообщений в session_messages после SA-T013

**Симптом:** В Codex-сессиях (`019d52e2`, `019d51c7`) `session_messages` содержит соседние дубли `(role, text)` — одно и то же сообщение записывается дважды подряд. Требуется ручное исправление `msg_count` (33→21, 27→17).

**Root cause:** SA-T013 добавил дедупликацию в одном code path, но не во всех. Codex-сессии могут использовать другой путь вставки (например через `archive-current` без `--agent codex` флага, или через другой branch в парсере).

**Повторялось:** 2+ раза подряд (обе сессии 2026-04-03).

**Fix:**
```python
def insert_messages(conn, session_id, messages):
    """Нормализовать дубли ДО сохранения в SQLite."""
    deduped = []
    prev = None
    for msg in messages:
        key = (msg['role'], msg['content'][:200])  # первые 200 символов как fingerprint
        if key == prev:
            continue  # skip adjacent duplicate
        deduped.append(msg)
        prev = key

    # Вставка только уникальных
    for i, msg in enumerate(deduped):
        conn.execute(
            "INSERT OR IGNORE INTO session_messages (session_id, seq, role, content) VALUES (?,?,?,?)",
            (session_id, i, msg['role'], msg['content'])
        )

    return len(deduped)
```

Проверить: дедупликация должна вызываться ПЕРЕД записью в SQLite во всех code path (не только в экспорте MD).

---

### BUG-OPEN-ISSUES-FMT — markdown `**` артефакты в поле open_issues

**Симптом:** `open_issues` содержит битую строку `"Статус S14:** done..."` — результат неполного strip markdown `**` при сохранении в JSON-колонку.

**Root cause:** Strip-логика удаляет `**` только с начала/конца строки, но не из середины. Если строка имеет вид `**Статус S14:** done...` — первые `**` удаляются, вторые остаются.

**Повторялось:** 1+ раз (2026-04-02, sproektirui 86f4b841).

**Fix:**
```python
import re

def strip_markdown(text: str) -> str:
    """Удалить markdown-форматирование для хранения в JSON-полях."""
    # Удалить bold/italic: **text** → text, *text* → text, __text__ → text
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
    # Удалить code: `code` → code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Удалить заголовки: ## Title → Title
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    return text.strip()

# Применять при формировании open_issues перед записью в sessions.open_issues
```

---

## Scope

- Добавить флаг `--keep-summary` в `archive-current` CLI
- Обеспечить overwrite guard для summary при повторной архивации (проверить all code paths)
- Вынести дедупликацию сообщений в единую функцию `insert_messages()`, вызываемую из всех paths
- Добавить `strip_markdown()` к формированию `open_issues`

## Out of scope

- Изменение формата Markdown-экспорта
- Изменение схемы SQLite

---

## Как протестировать

1. Запустить `archive-current --summary "Manual summary"` на сессии → затем повторно без `--summary` → summary не должен измениться
2. Запустить `archive-current --keep-summary` → summary сохранён, msg_count обновлён
3. Создать JSONL с дублями соседних сообщений → после архивации `session_messages` не содержит дублей
4. Создать open_issues с `**Статус:** done...` → в БД хранится без `**`

## Критерии приёмки

1. Повторная архивация не перезаписывает summary с `summary_manual=1`
2. msg_count в `sessions` равен фактическому числу уникальных сообщений
3. `sessions.open_issues` не содержит `**`, `__`, `##` артефактов
