**Дата:** 2026-04-03
**Статус:** done
**Завершено:** 2026-04-03
**Спецификация:** —

# SA-T034 — Исправить Artifacts: файлы из предыдущих сессий попадают в текущую

## Customer-facing инкремент

После архивирования сессии в `## Artifacts` будут только файлы, изменённые или прочитанные в этой конкретной сессии. Файлы из предшествующих сессий (verify-archive предыдущей сессии, предыдущий task) больше не будут попадать.

---

## Баги

### BUG-ARTIFACTS-WRONG-SESSION — артефакты из предыдущей сессии попадают в текущую

**Симптом:** `session_artifacts` содержит файлы, которые были изменены в предыдущей сессии, а не текущей:

Примеры из сессий:
- `(первое появление)`: Artifacts содержали `ADV-T016_s03_pipeline_runner.md (modified)`, `ADV-CHANGELOG.md (modified)`, `396fa6ae.md (modified)` — всё это файлы из работы по T016, которая была в предыдущей сессии
- `(повторение)`: Artifacts содержали `ADV-T017_s03_sqlite_state.md (modified)`, `state.go (modified)`, `state_test.go (created)` — накопленные файлы из предыдущей T017-сессии

**Повторялось:** 2+ раза.

**Root cause:** Скрипт захватывает tool calls из JSONL-файла без фильтрации по session_id. JSONL-файл накапливает сообщения из разных conversations/sessions. Если в начале нового conversation был вызван `/verify-archive` или `archive-current` для предыдущей сессии — их tool calls попадали в артефакты текущей сессии.

**Fix (реализовано):**

В `parse_claude_jsonl` добавлена фильтрация по `sessionId`: после определения `session_id` из первой записи, все последующие записи с другим `sessionId` пропускаются:

```python
# Skip entries from other sessions to avoid cross-session artifact contamination.
if session_id and entry_session_id and entry_session_id != session_id:
    continue
```

---

## Scope

- ✅ Добавить фильтрацию по session_id в `parse_claude_jsonl`
- ✅ Применить ко всем типам извлечения (artifacts, tasks, events — все идут через общий парсинг)

## Out of scope

- Ретроактивное исправление уже записанных сессий в БД
- Изменение структуры JSONL (это формат Claude Code, не наш)

---

## Критерии приёмки

1. ✅ Файлы из предыдущих verify-archive или archive-current вызовов не попадают в artifacts текущей сессии
2. ✅ Boundary корректно определяется по sessionId
3. ✅ Если JSONL содержит только одну сессию — поведение прежнее (sessionId совпадает)
