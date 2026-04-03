**Дата:** 2026-04-03
**Статус:** done 2026-04-03
**Спецификация:** —

# SA-T033 — Исправить Artifacts: shell-read trace (sed/rg/cat) не захватывается

## Customer-facing инкремент

После архивирования read-only сессии (intro, codereview, анализ кода) в `## Artifacts` появятся реально прочитанные файлы — `HANDOFF`, архитектурные доки, исходники, skill-файлы — а не пустой список или только 2 modified task docs.

---

## Баги

### BUG-ARTIFACTS-PARTIAL — shell-read trace через Bash tool теряется

**Симптом:** `session_artifacts` содержит только файлы из Write/Edit/apply_patch tool calls. Все файлы, прочитанные через Bash (`sed -n`, `cat`, `nl`, `tail`, `rg`, `grep`, `git log`, `git diff`, `sqlite3`), в артефакты не попадают.

Примеры:
- `019d4fa5`: 2 write-артефакта, потеряны `HANDOFF`, `architecture`, `go.mod`, `cmd/adv/main.go`, skill docs
- `019d51be`: 2 modified task docs, потерян read-trace: skill docs, `HANDOFF`, spec, кодовые файлы

**Повторялось:** 2+ раза в Codex-сессиях где основной инструмент чтения — Bash.

---

### BUG-ARTIFACTS-EMPTY — artifacts пусты когда нет file writes

**Симптом:** В сессиях без Write/Edit/apply_patch вообще `session_artifacts = []`, хотя прочитано 10–16 файлов через `sed -n`, `cat`, `nl`, `tail`.

Пример:
- `019d4f8b`: artifacts пусты; до архивации реально читались 16 файлов через `sed` и другие shell-read шаги

**Повторялось:** 1+ раз (и по природе баг воспроизводится в любой read-only сессии).

---

**Root cause:** Artifact extractor ориентирован только на write-операции:
- `Write` tool call → `created`
- `Edit`/`str_replace_editor` tool call → `modified`
- `apply_patch` → parse diff → `created`/`modified`/`deleted`

Bash tool calls (`exec_command`) не парсятся на предмет читаемых файлов. Нет regex-паттернов для `sed -n 'Xp' /path`, `cat /path`, `nl /path`, `tail -n N /path`, `rg pattern /path`, `git diff HEAD -- /path`, `git log -- /path`.

**Fix:**

Добавить в artifact extractor парсинг `exec_command` tool calls (Bash):

```python
SHELL_READ_PATTERNS = [
    # sed -n '1,50p' /path/to/file
    r"sed\s+['\"-][^'\"]*['\"]?\s+([^\s|>&]+)",
    # cat /path/to/file
    r"\bcat\s+([^\s|>&;]+)",
    # nl /path/to/file
    r"\bnl\s+([^\s|>&;]+)",
    # tail -n N /path/to/file  или  head -n N /path/to/file
    r"\b(?:tail|head)\s+(?:-[nf]\s+\d+\s+)?([^\s|>&;]+)",
    # rg pattern /path/to/file  или  grep pattern /path/to/file
    r"\b(?:rg|grep)\s+(?:-[^ ]+\s+)*([^\s|>&;]+\.(?:py|go|js|jsx|ts|tsx|md|yaml|json|toml|sql))",
    # git diff HEAD -- /path  или  git show HEAD:file
    r"git\s+(?:diff|show)\s+[^\s]+\s+(?:--\s+)?([^\s|>&;]+)",
    # git log -- /path
    r"git\s+log\s+.*?--\s+([^\s|>&;]+)",
    # sqlite3 /path/to/db "..."
    r"\bsqlite3\s+([^\s\"']+\.(?:db|sqlite|sqlite3))",
]
```

Условия для включения как `read` artifact:
- Путь должен начинаться с `/` (абсолютный) или содержать `/` (относительный с разрешением через `cwd`)
- Путь должен существовать (можно пропустить проверку, просто включать как best-effort)
- Не включать системные пути (`/usr/`, `/bin/`, `/etc/`, `/tmp/`)
- Не дублировать если уже есть запись с тем же путём

---

## Scope

- Добавить `parse_shell_reads(exec_command_text, cwd)` в artifact extractor
- Применить паттерны к tool calls типа `exec_command` / Bash
- Записывать найденные пути как `action='read'` в `session_artifacts`
- Дедуплицировать с уже существующими записями

## Out of scope

- Парсинг сложных pipe-цепочек с промежуточными файлами
- Верификация существования файла на диске (best-effort)
- Изменение write-ориентированной части (не трогать)

---

## Как протестировать

1. Заархивировать сессию где был `$intro` с чтением через `sed`/`cat` → artifacts должны содержать прочитанные файлы
2. Заархивировать read-only сессию (нет Edit/Write) → artifacts не должны быть пустыми
3. Проверить что дубли не создаются: если файл и Read-ed и cat-ed → одна запись `read`

## Критерии приёмки

1. `session_artifacts` не пуст для read-only сессий где были Bash-read команды
2. Файлы, прочитанные через `sed`/`cat`/`rg`/`git diff`, появляются с `action=read`
3. Системные пути (`/usr/bin/`, `/etc/`) не попадают в артефакты
4. Дублей по одному пути нет (уникальный constraint не нарушается)
