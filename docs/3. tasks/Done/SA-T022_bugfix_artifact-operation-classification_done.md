**Дата:** 2026-04-03
**Статус:** done
**Завершено:** 2026-04-03
**Спецификация:** —

# SA-T022 — Исправить классификацию операций артефактов (created vs modified, mv, A+D, cwd, is_error)

## Customer-facing инкремент

После архивирования сессии операции с файлами в `## Artifacts` будут точными: `modified` вместо `created` для существующих файлов, `moved` для `mv`-операций, корректное схлопывание `A+D` по одному пути. Файлы вне рабочей директории проекта не попадают в артефакты. Неудачные Edit-вызовы не попадают в дифы.

---

## Баги

### BUG-ARTIFACT-WRONG-OP — untracked файл помечается как created вместо modified

**Симптом:** Файл `go.mod` помечен `(created)`, хотя он существовал на диске и был изменён (восстановлена sqlite-зависимость). Файлы `contact.py`, `text.py` помечены `(modified)` — только читались. В целом: операция определяется по git-статусу (`??` untracked → `created`), а не по реальному состоянию на диске.

**Root cause:** Artifact classifier смотрит на git status файла:
- `??` (untracked) → `created`
- `M` (modified) → `modified`

Но файл может быть untracked (`??`) и при этом существовать физически на диске до сессии. Нужно проверять наличие файла до первого Write, а не git-статус.

**Повторялось:** 4+ раза, каждый раз исправляется вручную.

**Fix:**
```python
def classify_artifact_action(file_path, session_messages, git_status):
    # Если файл читался в сессии ДО первого write — это modified, не created
    first_read_idx = find_first_read_index(file_path, session_messages)
    first_write_idx = find_first_write_index(file_path, session_messages)

    if first_read_idx is not None and (
        first_write_idx is None or first_read_idx < first_write_idx
    ):
        return 'modified'  # существовал до записи

    # Дополнительно: проверить физическое существование файла до сессии
    # через session start snapshot или earliest tool evidence
    if git_status == '??' and file_existed_before_session(file_path, session_messages):
        return 'modified'

    return 'created'  # действительно новый
```

---

### BUG-ARTIFACT-MISSING-MOVE — после mv целевой путь не попадает в Artifacts

**Симптом:** После `mv task-file.md Done/task-file_done.md` (через Bash): исходный путь помечается `deleted`, но новый путь `Done/task-file_done.md` не появляется в Artifacts. В результате реально созданный файл отсутствует в архивной записи.

**Root cause:** Bash mv tracking фиксирует `deleted` исходного пути, но не добавляет целевой путь как новый артефакт. Нет парсинга `mv <src> <dst>` для добавления `<dst>` как `created` или `moved`.

**Повторялось:** появилось в 2+ сессиях.

**Fix:**
```python
# При парсинге exec_command с mv:
import re
mv_pattern = re.compile(r'\bmv\s+([^\s]+)\s+([^\s]+)')
for cmd in exec_commands:
    m = mv_pattern.search(cmd)
    if m:
        src, dst = m.group(1), m.group(2)
        # src → action='deleted' (или 'moved')
        # dst → action='created' (или 'moved')
        add_artifact(session_id, src, action='deleted')
        add_artifact(session_id, dst, action='created')
```

---

### BUG-ARTIFACT-WRONG-OP (вариант A+D) — apply_patch Delete+Add по одному пути даёт deleted

**Симптом:** Если один `apply_patch` делает `Delete File` + `Add File` для одного и того же пути (переписывает файл), архив пишет одновременно `A path` и `D path` и классифицирует surviving файл как `deleted`. Файл существует, но в артефактах числится удалённым.

**Root cause:** `apply_patch` output парсится построчно: нашли `D path` → записали deleted, нашли `A path` → записали created. При одинаковом пути `A+D` конфликтуют.

**Fix:**
```python
# После парсинга всех операций apply_patch — схлопывать по пути:
ops_by_path = defaultdict(set)
for op, path in parsed_ops:
    ops_by_path[path].add(op)

for path, ops in ops_by_path.items():
    if 'A' in ops and 'D' in ops:
        # Файл существует после операции → modified
        final_action = 'modified'
    elif 'A' in ops:
        final_action = 'created'
    elif 'D' in ops:
        final_action = 'deleted'
    add_artifact(session_id, path, final_action)
```

---

### BUG-ARTIFACTS-OUTSIDE-CWD — файлы вне рабочей директории проекта попадают в артефакты

**Симптом:** В `session_artifacts` появляется `~/.claude/settings.json` (и аналогичные пути) — Claude читает его при старте каждой сессии. Файл не относится к проекту, но попадает в Artifacts и генерирует synthetic diff всего settings.json.

**Root cause:** `extract_artifacts()` обрабатывает абсолютные пути без проверки принадлежности к `cwd`. Любой Read/Write вне директории проекта проходит без фильтрации.

**Повторялось:** в большинстве сессий (каждый раз settings.json исправляется вручную).

**Fix:**
```python
def extract_artifacts(tool_calls, cwd=None):
    cwd_resolved = str(Path(cwd).resolve()) if cwd else None
    # ...
    if cwd_resolved and path:
        abs_path = str(Path(path).expanduser().resolve())
        if not abs_path.startswith(cwd_resolved):
            continue  # вне проекта — пропустить
```

Исключения: пути начинающиеся с `~/.claude/`, `~/.codex/`, `/usr/`, `/opt/` — всегда вне проекта, всегда пропускать.

---

### BUG-DIFF-FAILED-EDIT-CAPTURED — неудачные Edit-вызовы попадают в дифы

**Симптом:** Когда Edit возвращает `is_error: true` ("String to replace not found"), payload этого вызова всё равно записывается в diff. В результате в `## Diffs` появляется hunk от неудачной попытки рядом с hunk от успешной — дублирующийся или некорректный diff.

**Root cause:** `_collect_tool_diff_hints()` строит diff из `old_string`/`new_string` payload Edit tool call не проверяя `is_error` в соответствующем tool result. Не проводится сопоставление с `_tool_results[tc_id]`.

**Повторялось:** BUG-DIFF-FAILED-EDIT-CAPTURED зафиксирован в BUGS.md, задачи не было.

**Fix:**
```python
# В parse_claude_jsonl: сохранять is_error вместе с tool results
_tool_errors = {}  # tool_use_id → bool
# при парсинге tool_result:
_tool_errors[tu_id] = bool(c.get("is_error"))

# В _collect_tool_diff_hints: пропускать failed calls
for tc in tool_calls:
    tc_id = tc.get("id")
    if tc_id and _tool_errors.get(tc_id):
        continue  # неудачный вызов — не включать в diff
    # ... остальная логика
```

Аналогично для `extract_artifacts`: файл, записанный только через неудачный Write, не должен попадать в артефакты.

---

## Scope

- Исправить artifact action classifier: физическое существование > git status
- Добавить парсинг `mv <src> <dst>` в exec_command для artifact tracking
- Схлопывать `A+D` по одному пути в `modified`
- Добавить cwd-фильтр: файлы вне директории проекта не попадают в артефакты
- Пробрасывать `is_error` из tool results в parse_claude_jsonl; фильтровать failed Edit/Write из артефактов и дифов

## Out of scope

- Изменение структуры `session_artifacts` таблицы
- Отслеживание `cp`, `ln`, `rsync` (только `mv`)

---

## Как протестировать

1. Сессия где untracked go.mod читался и потом изменялся → `action=modified`, не `created`
2. Сессия где task file перемещался `mv X Done/X` → оба пути в artifacts (`deleted` + `created`)
3. `apply_patch` с Delete+Add одного пути → единственная запись `(modified)`
4. Любая сессия → `~/.claude/settings.json` отсутствует в artifacts
5. Сессия с неудачным Edit ("String not found") → failed hunk не появляется в Diffs

## Критерии приёмки

1. Untracked файл, прочитанный до записи → `action=modified`
2. `mv src dst` → `src (deleted)` + `dst (created)` в artifacts
3. apply_patch `A+D` по одному пути → `(modified)`, не одновременно `(created)` и `(deleted)`
4. Файлы вне `cwd` (settings.json, ~/.codex/*, /usr/*) отсутствуют в artifacts
5. Edit с `is_error: true` не генерирует hunk в Diffs
