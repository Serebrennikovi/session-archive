**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T027 — Исправить парсинг Bash-команд: shell vars, task IDs, дубли диффов, mv/rm аргументы

## Customer-facing инкремент

После архивирования сессии: shell-переменные не появляются как артефакты, задачи перемещённые через Bash попадают в Tasks, один файл не даёт дублирующихся diff-блоков.

---

## Баги

### BUG-SHELL-VAR-AS-PATH — `$src`/`$dst` попадают как артефакты

**Симптом:** В сессии `a76647d6` в `session_artifacts` появились записи `file_path='$src'` и `file_path='$dst'` с action `moved_from`/`moved_to`. Скрипт распарсил `mv "$src" "$dst"` из bash-loop и захватил shell-переменные как пути.

**Root cause:** `extract_artifacts()` парсит `mv (\S+) (\S+)` после strip кавычек. Shell-переменные (`$src`, `$dst`, `$f`, `$file`) неотличимы от реальных путей по этому паттерну.

**Повторялось:** 1+ раз.

**Fix:**
```python
# В mv-детекторе extract_artifacts():
for m in re.finditer(r'\bmv\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))', cmd):
    src = m.group(1) or m.group(2) or m.group(3)
    dst = m.group(4) or m.group(5) or m.group(6)
    # Пропустить shell-переменные
    if src.startswith('$') or dst.startswith('$'):
        continue
    # Пропустить glob-паттерны
    if '*' in src or '?' in src:
        continue
    # Только если путь выглядит как реальный путь (содержит / или расширение)
    if '/' not in src and '.' not in src:
        continue
    artifacts.append({'file_path': src, 'action': 'moved_from'})
    artifacts.append({'file_path': dst, 'action': 'moved_to'})
```

---

### BUG-TASK-IDS-BASH-MOVE — задачи через `Bash mv` не попадают в Tasks

**Симптом:** В сессии `a76647d6` выполнялись SA-T009..T015, задачи перемещались через `Bash mv` (не через Edit/Write). Tasks оказались пустыми.

**Root cause:** `extract_task_ids()` смотрит только на Edit/Write/MultiEdit tool call `file_path`. Bash mv/cp/sed не сканируются на T-номера.

**Повторялось:** 1+ раз.

**Fix:**
```python
def extract_task_ids_from_bash(messages):
    """Дополнительный источник task IDs: Bash-команды с mv/cp/sed."""
    task_ids = set()
    task_pattern = re.compile(r'(?<![A-Za-z])([A-Z]{0,5}-?T\d{2,4})(?!\d)', re.IGNORECASE)

    for msg in messages:
        for tc in msg.get('tool_calls', []):
            if tc.get('name') != 'Bash':
                continue
            cmd = tc.get('input', {}).get('command', '')
            # Только mv/cp/sed/rename команды (не grep/cat/ls — там task IDs контекстные)
            if not re.match(r'\s*(mv|cp|rename|sed\s+.*-i)', cmd):
                continue
            for m in task_pattern.finditer(cmd):
                task_ids.add(m.group(1).upper())

    return task_ids
```

---

### BUG-MV-RM-PYTHON-ARGS / BUG-MV-RM-QUOTED-PATHS / BUG-MV-RM-SUMMARY-ARGS — mv/rm аргументы парсятся неверно

**Симптом:** (open bugs, проявляются при mv с кавычками и сложными аргументами)
- `mv -f "path with spaces/file.txt" "dest/"` — кавычки не учитываются
- `rm -rf "$(find . -name '*.tmp')"` — subshell захватывается как путь
- `python script.py --summary "some text" --output file.txt` — `--summary` arg захватывается

**Root cause:** mv/rm regex не обрабатывает quoted paths, subshell expressions, long flags.

**Повторялось:** Зарегистрированы как open.

**Fix:**
```python
import shlex

def parse_bash_mv_rm(cmd):
    """Безопасный парсинг mv/rm с учётом кавычек и флагов."""
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return []  # некорректная команда

    if not tokens:
        return []

    tool = tokens[0]
    if tool not in ('mv', 'rm', 'cp', 'rename'):
        return []

    # Отфильтровать флаги (начинаются с -)
    paths = [t for t in tokens[1:] if not t.startswith('-')]

    # Отфильтровать subshell expressions и shell vars
    paths = [p for p in paths
             if not p.startswith('$')
             and not p.startswith('`')
             and '$(find' not in p]

    return paths
```

---

### BUG-DIFF-DUPLICATE — один файл даёт два одинаковых diff-блока

**Симптом:** В сессии `37d18440` diff для `T288_done.md` появился дважды внутри одного diff-блока — скрипт добавил два `edit_snippet` из двух разных Edit-вызовов к одному файлу.

**Root cause:** При нескольких Edit-вызовах к одному файлу каждый вызов создаёт отдельный `edit_snippet`. Если содержимое одинаковое (draft→done, первый и второй Edit делают то же самое) — дубль.

**Повторялось:** 1+ раз.

**Fix:**
```python
def deduplicate_diffs(diffs):
    """
    Схлопнуть несколько diff-блоков для одного файла:
    1. Объединить hunks в порядке их появления
    2. Дедуплицировать идентичные hunks (по содержимому)
    """
    by_file = {}
    for d in diffs:
        path = d['file_path']
        if path not in by_file:
            by_file[path] = {'file_path': path, 'action': d['action'], 'hunks': []}
        for hunk in d.get('hunks', []):
            # Проверить дубль по содержимому hunk
            if hunk not in by_file[path]['hunks']:
                by_file[path]['hunks'].append(hunk)
    return list(by_file.values())
```

---

## Scope

- В `extract_artifacts()` mv-детектор: фильтровать `$var`, glob, non-path токены
- В `extract_task_ids()`: добавить сканирование Bash mv/cp/sed команд
- Добавить `parse_bash_mv_rm()` через `shlex.split()` для безопасного парсинга
- В diff-builder: добавить `deduplicate_diffs()` перед экспортом

## Out of scope

- Полный парсер bash-команд (только mv/rm/cp/rename)
- Обработка heredoc и multi-line bash

---

## Как протестировать

1. Сессия с `for f in *.md; do mv "$src" "$dst"; done` → `$src`/`$dst` не в артефактах
2. Сессия где задача перемещается через `mv SA-T015.md Done/` → T015 в session_tasks
3. Один файл редактируется дважды → в diff одна секция, не две

## Критерии приёмки

1. `session_artifacts` не содержит file_path начинающихся с `$`
2. Task IDs из `Bash mv path/SA-T015.md Done/` попадают в session_tasks
3. Два Edit-вызова на один файл → один diff-блок (не два)
