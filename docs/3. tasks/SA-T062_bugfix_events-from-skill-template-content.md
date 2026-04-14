**Дата:** 2026-04-09
**Статус:** draft
**Источник:** verify-archive сессии 5b1c21f7 (autodev-v2, ADV-T049 smoke test)

# SA-T062 — Ложные события из шаблонов скиллов

## Баг

Парсер извлекает event-типы из **текста шаблона скилла** (`<command-message>` expansion), а не из реальных действий сессии. Механизм аналогичен BUG-TASKS-PHANTOM-FROM-SKILL-EXAMPLES, но для Events.

## Воспроизведение (2026-04-09, session 5b1c21f7)

Сессия: smoke test T049 в autodev-v2. Вызван `/smoketest` через Skill tool.

Шаблон `/smoketest` содержит секцию с **примером** событий:
```markdown
## Events

- handoff_read
- tests_run
- session_archived
```

Это пример-заглушка в шаблоне, не реальные события.

**Результат в архиве:**
- `handoff_read` — записан как event ❌ (HANDOFF.md не читался ни одним Read tool call)
- `tests_run` — корректно (реально запускались go test)
- `session_archived` — корректно (реально вызван archive-session)

В сессии реально были: `tests_run` + `session_archived`. HANDOFF.md не открывался.

## Root cause

Event detector сканирует весь JSONL-контент (включая `<command-message>` expansions скиллов) и находит паттерны event-имён. Шаблон smoketest содержит литеральные строки `- handoff_read`, `- tests_run`, `- session_archived` как пример оформления — они детектируются как реальные события.

Аналогичная проблема в BUG-TASKS-PHANTOM-FROM-SKILL-EXAMPLES: task IDs из примеров шаблонов попадают в Tasks.

## Отличие от BUG-EVENTS-FROM-GIT-STATUS

BUG-EVENTS-FROM-GIT-STATUS: events из phantom **artifacts** (git status → artifact → cascade event detection).
Этот баг: events из **текста шаблонов скиллов** — прямое извлечение без artifact-посредника.

## Рекомендация

1. **Игнорировать `<command-message>` блоки** при event detection (те же блоки, что SA-T057 предлагает игнорировать для task extraction).
2. **Требовать evidence:** event `handoff_read` детектировать ТОЛЬКО при наличии Read tool call на файл с именем `HANDOFF*.md` или `HANDOFF` в пути — не по тексту в других контентах.
3. **Унифицировать:** фикс для SA-T057 (tasks from skill templates) должен применяться и к event detection.

## Воспроизведение #2 (2026-04-13, session 91ea9ed8, autodev-v2)

Сессия: `/fix T029`. Парсер записал event `spec_read`, но ни один spec-файл не читался через Read tool call. Реально читались: task doc T029, playbook (docs/5. Unsorted/), Go source files (task_worker.go, task_dag_scheduler.go, run.go, runner.go, interfaces.go, main.go). Event `spec_read` — ложный позитив, вероятно из контекста system-reminder или из содержимого прочитанных файлов (в которых упоминается "spec").

**Fix:** `spec_read` заменён на `task_read` в export .md.

## Acceptance Criteria

- [ ] `handoff_read` не детектируется из шаблона /smoketest
- [ ] Только реальные Read tool calls на HANDOFF.md → `handoff_read` event
- [ ] `spec_read`, `changelog_read` аналогично — только из Read tool calls, не из prose/templates
