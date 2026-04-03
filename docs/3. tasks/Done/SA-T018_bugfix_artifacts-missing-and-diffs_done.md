**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T018 — Исправить пропущенные артефакты и дифы изменённых файлов

## Customer-facing инкремент

После архивирования сессии все реально изменённые файлы (включая созданные bash-командами и перемещённые через /accept) будут присутствовать в Artifacts и иметь корректные дифы в секции Diffs.

---

## Баги

### BUG-ARTIFACTS-MISSING — изменённые файлы отсутствуют в Artifacts

**Симптом:** В `session_artifacts` отсутствуют файлы, реально созданные или изменённые в сессии:
- `state.go` (created), `state_test.go` (created) — созданы через Write/Edit, не захвачены
- `ADV-HANDOFF.md`, `ADV-CHANGELOG.md` — изменены через /accept, не попали в artifacts
- `go.sum` — создан командой `go mod download`, не числился в tool calls как Read/Write
- Главный файл задачи `ADV-T020_s03_worktree_manager.md` — отсутствовал в Artifacts

**Root cause:** Парсер artifacts строит список на основе tool calls (Read, Write, Edit, Glob). Файлы, модифицированные:
- bash-командами (shell-created: `go mod download`, `mv`, `cp`)
- через другие механизмы (IDE, внешние процессы)
- в рамках скиллов (/accept, /archive-session) которые работают в конце сессии

...не попадают в artifacts, так как не было явного Read/Write tool call для них в текущей сессии.

**Повторялось:** 5+ сессий.

**Fix:**
После сборки artifacts из tool calls — дополнительно запрашивать `git diff HEAD --name-only` и `git status --short`. Все tracked-файлы с изменениями (M, A, D, R) добавлять в artifacts если их нет. Action определять по статусу:
- `A` (added) → `created`
- `M` (modified) → `modified`
- `D` (deleted) → `deleted`
- `R` (renamed) → `moved_from` / `moved_to`

---

### BUG-DIFF-MISSING-TRACKED-FILES — дифы изменённых файлов отсутствуют в секции Diffs

**Симптом:** Секция `## Diffs` в MD-экспорте не содержит дифов для файлов, реально изменённых в сессии:
- `ADV-HANDOFF.md`, `ADV-CHANGELOG.md` — отсутствовали в Diffs, хотя tracked в git и изменены
- `runner.go`, `state.go` — изменены, но дифы не появились

**Root cause:** Скрипт генерирует git diff только для файлов, присутствующих в `session_artifacts`. Если файл не попал в artifacts (BUG-ARTIFACTS-MISSING), диф для него также не генерируется. Оба бага имеют общий root cause.

**Повторялось:** 3+ сессии.

**Fix:**
Тот же, что BUG-ARTIFACTS-MISSING: добавить `git diff HEAD --name-only` как fallback-источник списка файлов для генерации дифов. Для каждого tracked-modified файла, у которого нет диффа в session_artifacts — добавить диф из `git diff HEAD -- <file>`.

---

## Scope

- `session_archive.py`: после сборки artifacts из tool calls добавить шаг обогащения через `git diff HEAD --name-only` и `git status --short`
- Мержить два списка: из tool calls + из git status; дедуплицировать по `file_path`
- При отсутствии diff для tracked-modified файла — генерировать из `git diff HEAD -- <file>`
- Тесты: сессия с bash-created файлами и с /accept → все файлы в Artifacts и Diffs

## Out of scope

- Отслеживание файлов изменённых вне git (untracked изменения в непроиндексированных файлах)
- Ретроактивное обновление исторических сессий

---

## Как протестировать

1. Сессия с `go mod download` → архивировать → `go.sum` должен быть в Artifacts
2. Сессия с /accept (перемещение task-файла в Done/) → архивировать → оба пути (`moved_from`, `moved_to`) в Artifacts, HANDOFF.md и CHANGELOG.md с дифами в Diffs
3. Сессия с Write нового файла + bash-командой создающей ещё один файл → оба в Artifacts

## Критерии приёмки

1. Все файлы из `git diff HEAD --name-only` присутствуют в `session_artifacts`
2. Все tracked-modified файлы имеют диф в секции Diffs MD-экспорта
3. Дублирования не возникает (файл встречается в Artifacts один раз)
