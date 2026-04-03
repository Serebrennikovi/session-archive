# Спецификация: Context-Window Whitelist для session boundary

**ID:** SA-S01
**Статус:** draft
**Версия:** 1.0
**Дата:** 2026-04-03

---

## Цель

Заменить JSONL-based session boundary detection (sessionId + timestamp фильтр) на **whitelist из контекстного окна**: скилл `archive-session` передаёт в Python список tool_call_ids, которые Claude видел в своём контексте. Python использует его как первичный фильтр при парсинге JSONL.

Это решает целый класс багов (BUG-JSONL-CROSS-SESSION-REGRESSION и его вариации), которые раз за разом регрессируют, потому что JSONL накапливает несколько сессий и граница сессии из него не выводится надёжно. Контекстное окно чата = и есть текущая сессия, без ambiguity.

---

## Scope

### Входит:
- Новый CLI аргумент `--tool-ids` в `archive-current` (JSON-массив tool_call_ids)
- `parse_claude_jsonl`: при наличии `--tool-ids` фильтровать tool_calls по whitelist вместо sessionId
- Обновление скилла `archive-session.md`: Claude перечисляет tool_call_ids из своего контекста перед вызовом скрипта
- Fallback: если `--tool-ids` не передан — поведение без изменений (sessionId-фильтр как сейчас)

### Не входит:
- Рефакторинг events/tags/tasks extraction (это отдельные задачи)
- BUG-MV-QUOTED-PATHS-WITH-SPACES, BUG-HANDOFF-READ-OVERWRITE и другие баги не связанные с session boundary
- verify-archive (там контекст недоступен — используется fallback)

---

## Архитектура и структура

### Текущий поток

```
/archive-session
  → Python find_current_jsonl()
  → parse_claude_jsonl(jsonl_path)
      → читает ВСЕ entries
      → определяет session_id из первой записи
      → фильтрует entries: entry_session_id != session_id → skip
      → [проблема: если несколько сессий в одном JSONL с одинаковым session_id
         или без session_id — фильтр не работает]
  → extract_artifacts(tool_calls)
```

### Новый поток

```
/archive-session
  → Claude перечисляет все tool_call_ids из своего контекста
  → Python archive-current --tool-ids '["toolu_01...", "toolu_02...", ...]'
  → parse_claude_jsonl(jsonl_path, tool_id_whitelist={...})
      → читает entries
      → tool_use content block: включать только если id IN whitelist
      → всё остальное (messages, metadata) — без изменений
  → extract_artifacts(tool_calls)  ← только whitelisted calls
```

### Как Claude получает tool_call_ids

В Claude Code каждый tool_use content block имеет уникальный `id` (формат `toolu_01...`). Эти IDs видны Claude в его контексте как часть conversation history. Скилл `archive-session` инструктирует Claude собрать все tool_use IDs из текущей сессии перед вызовом скрипта.

Конкретно: Claude итерирует по своей истории tool calls в обратном порядке и выдаёт JSON-массив строк. Это детерминированно и не требует доп. tool calls.

### Fallback для verify/rerun

`verify-archive` и `rerun` не имеют оригинального контекста → `--tool-ids` не передаётся → `parse_claude_jsonl` работает как сейчас (sessionId-фильтр). Поведение не деградирует.

---

## Изменения в БД

Нет. Schema не меняется.

---

## CLI интерфейс

### Новый аргумент `archive-current`

```
python3 session_archive.py archive-current \
  --tool-ids '["toolu_01abc123", "toolu_02def456", ...]' \
  [--summary "..."] [--model ...] [--cwd ...]
```

**Аргумент:** `--tool-ids <json-array>`
**Тип:** JSON-строка, массив строк (tool_call_ids)
**Опциональный:** да. Если отсутствует — поведение без изменений.

### Изменения в parse_archive_current_args

```python
parser.add_argument("--tool-ids", default=None,
    help="JSON array of tool_call_ids from context window (whitelist filter)")
```

### Изменения в parse_claude_jsonl

```python
def parse_claude_jsonl(jsonl_path, tool_id_whitelist=None):
    ...
    elif ctype == "tool_use":
        tc_id = c.get("id")
        # Whitelist filter: если whitelist задан и ID не в нём — пропускаем
        if tool_id_whitelist is not None and tc_id not in tool_id_whitelist:
            continue
        tool_calls.append({...})
```

`tool_id_whitelist` — `set[str]` или `None`. Формируется в `cmd_archive_current` из `opts["tool_ids"]`.

---

## Изменения в скилле archive-session

В `~/.claude/commands/archive-session.md` добавить шаг перед вызовом скрипта:

```
Перед вызовом python3 session_archive.py archive-current:
1. Собери все tool_call_ids из текущей сессии (все tool_use вызовы которые ты сделал).
   Формат: JSON-массив строк, например: ["toolu_01abc", "toolu_02def", ...]
2. Передай их через --tool-ids '<json>'
```

---

## Acceptance Criteria / DoD

- [ ] `archive-current --tool-ids '[...]'` принимает аргумент без ошибок
- [ ] При наличии `--tool-ids`: в `tool_calls` попадают только записи с ID из whitelist
- [ ] При наличии `--tool-ids`: артефакты из предыдущих сессий (другие tool_call_ids) не попадают в результат
- [ ] При отсутствии `--tool-ids`: поведение идентично текущему (sessionId-фильтр)
- [ ] Скилл `archive-session` передаёт `--tool-ids` с реальными IDs из контекста
- [ ] BUG-JSONL-CROSS-SESSION-REGRESSION не воспроизводится после архивации с новым скиллом
- [ ] verify-archive (без `--tool-ids`) продолжает работать

---

## Тест-план

1. Запустить две сессии подряд без коммита между ними (оба в одном JSONL)
2. Заархивировать вторую сессию с `--tool-ids` (IDs только второй сессии)
3. Проверить: artifacts не содержат файлов из первой сессии
4. Заархивировать ту же сессию без `--tool-ids` → убедиться что fallback работает (даже если менее точно)
5. Запустить verify-archive на заархивированной сессии → должен работать без изменений

---

## Зависимости

- Требуется до начала: нет (изменения локальные в `parse_claude_jsonl` + `cmd_archive_current` + скилл)
- Блокирует: SA-T037 (задача реализации)

---

## Риски

- **Неполный whitelist:** если скилл пропустит часть tool_call_ids (например из-за context compaction в длинных сессиях) — часть артефактов может пропасть. Митигация: при compaction Claude всё равно помнит что делал (summary содержит actions). Дополнительно: если `--tool-ids` пустой массив → считать как отсутствующий и использовать fallback.
- **Видимость IDs:** Claude видит tool_use_id в своём контексте, но формат (`toolu_01...`) зависит от API. Если формат изменится — нужна проверка. Митигация: парсер проверяет что ID из whitelist действительно встречаются в JSONL; если ни один не нашёлся → warning + fallback.

---

## Связанные документы

- Архитектура: [SA-architecture.md](../SA-architecture.md)
- Зависит от: нет
- Задача реализации: [SA-T037](../3.%20tasks/SA-T037_s01_context-window-whitelist.md)
- Затрагивает баги: BUG-JSONL-CROSS-SESSION-REGRESSION, BUG-ARTIFACT-INCOMPLETE (частично), BUG-TASKS-FROM-PREV-SESSION, BUG-TAGS-WRONG-SKILL (частично)
