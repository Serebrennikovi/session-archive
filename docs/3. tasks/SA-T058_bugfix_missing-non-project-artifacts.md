**Дата:** 2026-04-08
**Статус:** draft
**Источник:** verify-archive сессии 6210a39a

# SA-T058 — Артефакты вне project_path не захватываются

## Баг

Файлы за пределами `project_path` не попадают в artifacts, даже если с ними активно работали (Edit/Write).

**Воспроизведение:** сессия 6210a39a в проекте `/Users/is/personal/Projects/09_AutoDev_v2`:
- `~/.claude/commands/smoketest.md` — 4 Edit-вызова (autoresearch). **Не в artifacts.**
- `~/.claude/commands/smoketest.backup.2026-04-08.md` — создан через Bash cp. **Не в artifacts.**
- `internal/runner/smoketest_integration_test.go` — создан Write, удалён rm. **Не в artifacts.**

**Причина:** artifact extraction фильтрует по `project_path` prefix. Файлы в `~/.claude/commands/` не матчат.

**Impact:** ключевая работа сессии (улучшение скилла через autoresearch) не отражена в архиве.

### Новое воспроизведение (2026-04-08, session 336dd55e)

Сессия в проекте autodev-v2 модифицировала:
- `~/.claude/commands/codereview.md` — 3 Edit-вызова (добавление stale pointer rule + AutoResearch checklist item). **Не в artifacts, не в diffs.**
- `~/.claude/commands/smoketest.md` — 2 Edit-вызова (добавление DB round-trip rule + AutoResearch checklist item). **Не в artifacts, не в diffs.**

Идентичный root cause: `project_path` prefix filter.

### Новое воспроизведение (2026-04-09, session ee202e0b)

Сессия в проекте autodev-v2 модифицировала:
- `~/.claude/commands/codereview.md` — 3 Edit-вызова (Фаза B7 #6b + B8 #d + checklist). **Не в artifacts, не в diffs.**
- `~/.claude/commands/smoketest.md` — 2 Edit-вызова (шаг 2e + checklist). **Не в artifacts, не в diffs.**

Исправлено вручную в export .md + SQLite через `/verify-archive`.

### Новое воспроизведение (2026-04-09, session bd314e97)

Сессия в проекте autodev-v2 модифицировала:
- `~/.claude/commands/codereview.md` — 2 Edit-вызова (Phase B7 items 10-11, AutoResearch items 12-13). **Не в artifacts, не в diffs.**
- `~/.claude/commands/smoketest.md` — 3 Edit-вызова (category J, pollution/flakiness checks, AutoResearch items 9-10). **Не в artifacts, не в diffs.**

Идентичный root cause: `project_path` prefix filter.

Исправлено вручную в export .md + SQLite через `/verify-archive`.

### Новое воспроизведение (2026-04-12, session 0368108d)

Сессия в проекте autodev-v2 модифицировала:
- `~/.claude/commands/codereview.md` — 2 Edit-вызова (Фаза E: Finding Verification Gate + AutoResearch checklist #20). **Не в artifacts, не в diffs.**
- `~/.claude/commands/smoketest.md` — 2 Edit-вызова (Шаг 6b: Finding Verification Gate + AutoResearch checklist #13). **Не в artifacts, не в diffs.**

Исправлено вручную в export .md + SQLite через `/verify-archive`.

### Новое воспроизведение (2026-04-13, session 57aa5359)

Сессия в проекте 13_Week модифицировала:
- `/Users/is/sales/06_ING_ingingo/06_ING_intro.md` — Read + 2 Edit (обновление статуса Ingingo deal + запись условий оффера). **Не в artifacts, не в diffs.**
- `/Users/is/.claude/projects/-Users-is-personal-Projects-13-Week/memory/daily_routine.md` — Read + Write (обновление распорядка дня). **Не в artifacts, не в diffs.**
- `/Users/is/.claude/projects/-Users-is-personal-Projects-13-Week/memory/MEMORY.md` — Read. **Не в artifacts.**

Идентичный root cause: `project_path` prefix filter.

### Новое воспроизведение (2026-04-13, session de196494)

Сессия в проекте sales модифицировала:
- `/Users/is/.claude/projects/-Users-is-sales/memory/MEMORY.md` — Read + 2 Edit (добавление секций Project и Feedback). **Не в artifacts, не в diffs.**
- `/Users/is/.claude/projects/-Users-is-sales/memory/arbitra_people.md` — Write (создание memory про людей Arbitra). **Не в artifacts.**
- `/Users/is/.claude/projects/-Users-is-sales/memory/feedback_arbitra_style.md` — Write (создание memory про предпочтение Stripe-стиля). **Не в artifacts.**

Идентичный root cause: `project_path` prefix filter. Memory-файлы в `~/.claude/projects/` не матчат `/Users/is/sales`.

Исправлено вручную в export .md через `/verify-archive`.

### Новое воспроизведение (2026-04-13, session 410df60f)

Сессия в проекте autodev-v2 модифицировала:
- `~/.claude/commands/codereview.md` — 2 Edit-вызова (Phase B10 orchestration audit + AutoResearch #22). **Не в artifacts, не в diffs.**
- `~/.claude/commands/smoketest.md` — 2 Edit-вызова (orchestration wiring gate + AutoResearch #14). **Не в artifacts, не в diffs.**
- `~/.claude/commands/codereview-free.md` — 1 Edit-вызов (bug class vocabulary). **Не в artifacts, не в diffs.**

Вместо этих файлов artifacts содержали 20 phantom-файлов из `git status` (SA-T060). Исправлено вручную через `/verify-archive`.

## Рекомендация

1. Расширить artifact extraction: включать все файлы из Edit/Write tool calls, не только project_path
2. Для файлов вне project_path — хранить полный абсолютный путь
3. Для created+deleted файлов (temp test files) — отмечать как `(created+deleted)` в action
