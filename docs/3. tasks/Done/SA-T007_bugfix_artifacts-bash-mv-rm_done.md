**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T007 — Исправить Artifacts: mv/rm через Bash не детектируются

## Customer-facing инкремент

После исправления артефакты будут корректно отражать `deleted` и `moved` статусы файлов, удалённых или перемещённых через Bash-команды (`rm`, `mv`). Не нужно вручную исправлять action в SQLite после каждой сессии с accept/deploy.

---

## Баги

### BUG-NEW — Renamed/moved файлы не отслеживаются

**Симптом:** Файл перемещён через `mv` (Bash tool) — например, task-файл переносится в `Done/`. В `session_artifacts` записан старый путь со статусом `modified`; новый путь в Done-папке полностью отсутствует. При проверке через git — старый путь показывается как `D`, новый как `A`.

**Root cause:** Скрипт строит список артефактов по Write/Edit tool-calls из JSONL. Bash-команды (`mv`, `cp`, `rename`) не парсятся как artifact-events. В результате:
- Последний Edit-call на файл до `mv` → action=`modified` (неверно)
- Новый путь не появляется вовсе

**Повторялось:** 11+ раз (BUG-NEW во всех сессиях с accept/archive).

**Fix (два подхода, оба нужны):**

**A) Парсить `mv`/`rm` из Bash tool_use:**
```python
# В extract_artifacts():
for tool_call in tool_uses:
    if tool_call['name'] == 'Bash':
        cmd = tool_call['input'].get('command', '')
        # mv src dst
        mv_match = re.findall(r'\bmv\s+(\S+)\s+(\S+)', cmd)
        for src, dst in mv_match:
            artifacts[src] = 'moved_from'
            artifacts[dst] = 'moved_to'
        # rm src
        rm_match = re.findall(r'\brm\s+(?:-[rf]+\s+)?(\S+)', cmd)
        for path in rm_match:
            artifacts[path] = 'deleted'
```

**B) Post-check существования файла:**
После сборки списка артефактов — проверить каждый файл на диске:
```python
for path, action in artifacts.items():
    if action in ('modified', 'created') and not os.path.exists(path):
        artifacts[path] = 'deleted'
```

---

### BUG-ARTIFACTS-WRONG-ACTION — Edit → rm: action остаётся `modified`

**Симптом:** Файл редактировался (Edit) а затем удалялся (rm) в одной сессии. Скрипт помечает его как `modified` — от последнего Edit. Реальный статус: `deleted`.

**Root cause:** Artifact-action определяется последним Write/Edit tool-call. `rm` через Bash не регистрируется. Порядок: Edit (→ `modified`) → Bash rm (не видно) → итог: `modified`.

**Повторялось:** 4+ раза (BUG-ARTIFACTS-WRONG-ACTION в сессиях с codereview + accept).

**Fix:** Подход B из BUG-NEW выше — post-check существования файла покрывает этот кейс автоматически.

---

## Scope

- Добавить парсинг Bash-команд `mv`/`rm` в `extract_artifacts()` (или аналог) в `session_archive.py`
- Добавить post-check существования файла для каждого артефакта после сборки списка
- Корректно разрешать коллизии: если файл был `created` и затем `deleted` в одной сессии — удалить из списка (не писать ephemeral артефакты)

## Out of scope

- Отслеживание `cp` (копирование — отдельный случай)
- Артефакты вне `cwd` проекта

---

## Как протестировать

1. Провести сессию: создать файл через Write, затем `mv` его в другую папку
2. Запустить `/archive-session`
3. Проверить `session_artifacts` — исходный путь = `moved_from`, новый путь = `moved_to` (или `created`)
4. Провести сессию: Edit файл, затем Bash `rm`
5. Проверить — action = `deleted`, не `modified`

## Критерии приёмки

1. После `mv task.md Done/task_done.md` → artifacts: `task.md (moved_from)` + `Done/task_done.md (moved_to)`
2. После Edit → rm → artifacts: `file.md (deleted)`
3. Файлы проверяются на существование перед записью action
