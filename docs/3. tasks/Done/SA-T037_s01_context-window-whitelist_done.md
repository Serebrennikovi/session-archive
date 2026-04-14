**Дата:** 2026-04-03
**Статус:** done
**Дата завершения:** 2026-04-03
**Спецификация:** [docs/2. specifications/SA-S01_context-window-whitelist.md](../2.%20specifications/SA-S01_context-window-whitelist.md)

# SA-T037_s01_context-window-whitelist — Whitelist tool_call_ids из контекста для session boundary

## Customer-facing инкремент

Скилл `/archive-session` передаёт в Python список tool_call_ids из контекстного окна → скрипт использует его как whitelist при парсинге JSONL. Артефакты, задачи и события из других сессий (BUG-JSONL-CROSS-SESSION-REGRESSION) перестают попадать в архив текущей сессии.

---

## Scope

- `parse_archive_current_args`: добавить аргумент `--tool-ids <json-array>`
- `cmd_archive_current`: парсить `--tool-ids`, передавать в `parse_jsonl` как `tool_id_whitelist`
- `parse_claude_jsonl`: добавить параметр `tool_id_whitelist: set[str] | None`; при парсинге `tool_use` content block — пропускать если `id not in whitelist` (только когда whitelist задан и непустой)
- `~/.claude/commands/archive-session.md`: добавить шаг перед вызовом скрипта — Claude собирает все tool_call_ids из своего контекста и передаёт через `--tool-ids`

## Out of scope

- Изменения в events/tags/tasks extraction (они уже получают отфильтрованный `tool_calls`)
- Изменения в verify-archive, rerun, cmd_write (там whitelist не нужен → fallback)
- Исправление других открытых багов (BUG-MV-QUOTED-PATHS, BUG-HANDOFF-READ-OVERWRITE и т.д.)

---

## Реализация

### 1. `parse_archive_current_args` — новый аргумент

```python
p.add_argument("--tool-ids", default=None,
    help="JSON array of tool_call_ids observed in context window")
```

### 2. `cmd_archive_current` — передача whitelist

```python
tool_id_whitelist = None
if opts.get("tool_ids"):
    try:
        ids = json.loads(opts["tool_ids"])
        if isinstance(ids, list) and ids:
            tool_id_whitelist = set(ids)
    except (json.JSONDecodeError, TypeError):
        pass  # невалидный JSON → игнорируем, используем fallback

data = parse_jsonl(session_info["jsonl_path"], tool_id_whitelist=tool_id_whitelist)
```

### 3. `parse_claude_jsonl` — whitelist filter

```python
def parse_claude_jsonl(jsonl_path, tool_id_whitelist=None):
    ...
    elif ctype == "tool_use":
        tc_id = c.get("id")
        if tool_id_whitelist is not None and tc_id not in tool_id_whitelist:
            continue  # skip tool calls from other sessions
        tool_calls.append({...})
```

> `parse_jsonl` — обёртка над `parse_claude_jsonl`, нужно пробросить `tool_id_whitelist` через неё.

### 4. `archive-session.md` — сбор IDs в скилле

Добавить перед блоком вызова скрипта:

```
Перед вызовом python3 session_archive.py archive-current собери все tool_call_ids
из текущей сессии (каждый tool_use вызов имеет уникальный id вида toolu_01...).
Передай их через --tool-ids '<json-array>'.

Пример: --tool-ids '["toolu_01abc123def", "toolu_02xyz456ghi"]'

Если tool_call_ids недоступны — не передавай аргумент (скрипт использует fallback).
```

---

## Как протестировать

1. Запустить две сессии подряд без коммита между ними (оба в одном JSONL-файле)
2. Заархивировать вторую сессию с `--tool-ids '[<ids только второй сессии>]'`
3. Проверить `session_artifacts` в SQLite — не должно быть файлов из первой сессии
4. Запустить архивацию без `--tool-ids` — убедиться что fallback (sessionId-фильтр) работает
5. Передать `--tool-ids '[]'` (пустой массив) — должен использоваться fallback, не фильтровать всё
6. Передать `--tool-ids 'не-json'` — не должно падать с ошибкой

---

## Критерии приёмки

1. `archive-current --tool-ids '[...]'` принимает аргумент без ошибок
2. При непустом whitelist: в `tool_calls` попадают только записи с ID из списка
3. При пустом массиве или невалидном JSON: поведение = без `--tool-ids` (fallback)
4. Скилл `archive-session.md` передаёт `--tool-ids` с реальными IDs из контекста
5. После архивации с новым скиллом: artifacts не содержат файлов из предыдущей сессии в том же JSONL
