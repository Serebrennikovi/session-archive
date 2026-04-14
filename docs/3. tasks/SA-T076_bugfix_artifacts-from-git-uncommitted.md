**Дата:** 2026-04-09
**Статус:** open
**Sev:** MEDIUM

# SA-T076 — Artifacts: ложные (modified) артефакты из git uncommitted

## Проблема

Секция `## Artifacts` содержит файлы с пометкой `(modified)`, которые были изменены в предыдущих сессиях, не в текущей.

## Воспроизведение

Сессия `33b531d7` — artifacts содержат 5 файлов `(modified)`, из которых 4 изменены в предыдущих сессиях:
- `.claude/commands/codereview-local.md` (modified) — НЕ эта сессия
- `.claude/settings.local.json` (modified) — НЕ эта сессия
- `T151_s15_series_popup_from_selection.md` (modified) — НЕ эта сессия
- `T153_s15_installation_visualization.md` (modified) — НЕ эта сессия
- `e2e/report/index.html` (modified) — НЕ эта сессия

## Root cause

Артефакты с action `(modified)` определяются из git diff, а не из tool calls сессии. Тот же root cause что SA-T075.

## Рекомендация

Артефакты `(modified)` должны определяться из Edit/Write tool calls в JSONL, а не из `git status`/`git diff`.

### Воспроизведение #2 (2026-04-11, session a1d889f9, autodev-v2)

`/codereview t052` — реально сессия изменила только `ADV-T052_s04_runner_state_durability.md` (append review section через Edit tool). В `session_artifacts` SQLite попал лишний `docs/3. tasks/ADV-S06_spec_hardening_for_draft_packages/ADV-T033_s06_cli_plan_context_runner.md` с action=`modified`, diff_source=`git_head` — этот файл НЕ трогался в сессии вообще (ни Read, ни Edit). Попал исключительно из-за того что он в uncommitted working tree на ветке `codex/pipeline-hardening-stageb-finalize`.

Важное уточнение: в этой сессии БЫЛИ `Read`-операции для 5 project-файлов (runner.go, runner_test.go, smoke_t052_test.go, handoff_sync.go, codereview-local.md) — они корректно попали как `(read)`. Но лишний T033 пришёл из git diff, что подтверждает: два источника артефактов (tool-calls vs git-diff) мёрджатся без пересечения, и git-diff добавляет phantom-записи даже когда parser уже имеет точный список Edit-файлов.

**Fix:** удалён из SQLite `session_artifacts` и из export.md `## Artifacts` + `## Diffs`.

### Воспроизведение #3 (2026-04-11, session fa809fcb, autodev-v2)

`/fix T045` — сессия изменила 2 файла (T045 task doc + adv_native_parity_test.go). В `session_artifacts` попали 5 лишних файлов с action=`modified`:
- `PROMPTS/plan_spec_critic.md` — T034 fix (предыдущая сессия)
- `cmd/adv/main.go` — T034 fix
- `cmd/adv/plan_test.go` — T034 fix
- `internal/plan/findings/findings_test.go` — T034 fix
- `internal/plan/findings/writer.go` — T034 fix

Также `T034_...md` попал как `modified` вместо `read` (diff из git, но в сессии только grep/read).

**Fix:** удалены 5 phantom artifacts из SQLite + T034 action→read; удалены 6 diff-блоков (519 строк) из export.md.

### Воспроизведение #4 (2026-04-12, session a8e931c1, autodev-v2)

Сессия реально работала с:
- Read: HANDOFF, architecture, S06/S07/S08 specs, T045, T044, task_decomposition_guide.md (12+ Read calls)
- Write: T055, T056 (created)
- Edit: HANDOFF (2×)

В artifacts попали 6 ложных файлов с `(modified)` из git uncommitted:
- `PROMPTS/plan_spec_critic.md` — T034 (предыдущая сессия)
- `cmd/adv/main.go` — T034
- `cmd/adv/plan_test.go` — T034
- `internal/plan/findings/findings_test.go` — T034
- `internal/plan/findings/writer.go` — T034
- `tests/integration/adv_native_parity_test.go` — T045 (предыдущая сессия)

Отсутствуют: 2 созданных файла (T055, T056), 8+ прочитанных файлов (specs, guides, architecture).

### Воспроизведение #5 (2026-04-12, session 7eea8025, autodev-v2)

Сессия `/codereview T034` реально работала с:
- Read: writer.go, parser.go, types.go, critic.go, evaluator.go, main.go, plan_test.go, findings_test.go, plan_spec_critic.md, HANDOFF.md (10+ Read calls)
- Edit: T034 task file (3× append)

В artifacts попали 5 ложных файлов с `(modified)` из git uncommitted:
- `PROMPTS/plan_spec_critic.md` — T034 prior fix session
- `cmd/adv/main.go` — T034 prior fix session
- `cmd/adv/plan_test.go` — T034 prior fix session
- `internal/plan/findings/findings_test.go` — T034 prior fix session
- `internal/plan/findings/writer.go` — T034 prior fix session

Все 5 файлов БЫЛИ прочитаны в этой сессии (корректно), но получили action=`modified` вместо `read` из-за `git diff HEAD`.

**Fix:** Phantom `modified` записи удалены из SQLite, заменены на `read`. Export artifacts секция исправлена.

### Воспроизведение #6 (2026-04-13, session 852dae4d, autodev-v2)

Сессия `/smoketest T026` реально работала с:
- Read: HANDOFF, T026 task file, 6 Go source files (scheduler, worker, interfaces, config, test, run.go), state.go, worktree.go
- Edit: T026 task file (1× append Smoke Test секция)
- Created+Deleted: smoketest_t026_test.go (temp smoke test file)

В artifacts попали 12 ложных файлов с `(modified)`/`(deleted)` из git uncommitted:
- `adv` (binary), `cmd/adv/main.go`, `docs/2. specifications/ADV-S05_...`, `docs/2. specifications/ADV-S06_...`, `docs/ADV-CHANGELOG.md`, `docs/ADV-architecture.md`, `internal/plan/findings/findings_test.go`, `internal/worktree/worktree_test.go` — all modified in prior sessions
- `docs/3. tasks/.../ADV-T046_...`, `docs/3. tasks/.../ADV-T035_...` — deleted in prior sessions
- `docs/3. tasks/.../ADV-T055_...`, `docs/3. tasks/.../ADV-T056_...` — modified in prior sessions

**Fix:** 12 phantom artifacts удалены из SQLite. `manually_reviewed = 1`.

### Воспроизведение #7 (2026-04-13, session `ba9d7314`, autodev-v2)

`/codereview t026` — сессия изменила только `ADV-T026_s05_task_dag_scheduler.md`. В artifacts попало 13 лишних файлов из uncommitted working tree (binary `adv`, `cmd/adv/main.go`, `worktree.go`, `findings_test.go`, ADV-S06/S07 specs, CHANGELOG, HANDOFF и т.д.), плюс их полные diffs (включая 5MB binary patch для `adv`). Export markdown вырос до 268KB (вместо ~20KB). Самый масштабный случай — 13 phantom artifacts из 24 total (54%).

**Fix:** 13 phantom artifacts удалены из SQLite. 2767 строк bogus diffs удалены из export. `go.sum` (не читался явно) также удалён.

### Воспроизведение #8 (2026-04-13, session `91ea9ed8`, autodev-v2)

`/fix T029` — сессия изменила 4 файла: `cmd/adv/main.go`, `task_dag_scheduler.go`, `task_worker.go`, `ADV-T029_...md`. В artifacts попали 11 лишних файлов из uncommitted working tree (`adv` binary, `main_test.go`, `ADV-S05_...md`, `ADV-CHANGELOG.md`, `ADV-HANDOFF.md`, `run.go`, `runner.go`, `interfaces.go`, `state.go`, `state_test.go`, `worktree.go`). Все относятся к Codex branch changes, не к текущей сессии.

**Fix:** 11 phantom artifacts удалены из SQLite и export .md.

### Воспроизведение #9 (2026-04-13, session `cde4f5f3`, autodev-v2)

Исследовательская сессия (WebSearch ×5, Write ×1). Реально создан 1 файл: `agent_labor_marketplaces_research.md`. В artifacts попали 20 ложных файлов с `(modified)`/`(deleted)` из git uncommitted — все от предыдущих сессий на ветке `codex/pipeline-hardening-stageb-finalize`.

**Fix:** 20 phantom artifacts удалены из SQLite. `manually_reviewed = 1`.

### Воспроизведение #10 (2026-04-13, session `2ab24fa4`, sproektirui)

Сессия: Trello triage + cache-bust fix (`admin.py`). Реально изменён 1 repo-файл. В artifacts попали 8 ложных файлов от предыдущей сессии (T149/T153): `PrivacyPage.jsx` (modified), `e2e/report/index.html` (modified), 6× `e2e/screenshots/review/t153-*.png` (modified). Все — uncommitted changes + cross-session contamination через shared JSONL.

**Fix:** 8 phantom artifacts удалены из SQLite. 3 корректных добавлены (`admin.py`, `feedback_trello_move_rules.md`, `MEMORY.md`). `manually_reviewed = 1`.

### Воспроизведение #N (2026-04-14, session `21dee077`, autodev-v2)

`/codereview T036` — сессия реально прочитала 11 файлов (evaluator.go, summary.go, freeze_test.go, critic.go, repair.go, parser.go, types.go, explain.go, HANDOFF, CHANGELOG, T036 task file) и изменила 1 файл (T036 task file — append Code Review section).

В artifacts попали **34 ложных файла** с `(modified)`/`(deleted)` из git uncommitted — включая `adv` binary, `cmd/adv/main.go`, `internal/dag/*.go`, `internal/scheduler/*.go`, `internal/runner/*.go`, `internal/state/*.go`, 14 task docs из S05/S07/S08 и т.д. Ни один из этих 34 файлов не трогался в текущей сессии (ни Read, ни Edit).

**Fix:** 34 phantom artifacts заменены на 11 корректных (1 modified + 10 read). `tool_call_count` 4→25.

**Повторная контаминация (2026-04-14, --force re-archive):** `archive-current --force` на ту же сессию 21dee077 снова записал 42 artifact (35 phantom). Баг воспроизводится стабильно при каждом re-archive. Повторная чистка: 35 phantom удалено, 7 корректных оставлено (5 modified + 2 read).

### Воспроизведение #N (2026-04-14, session `c60ad134`, autodev-v2)

Сессия: исследование tooling + настройка hooks в `~/.claude/settings.json`. 0 Edit/Write на repo-файлы. В artifacts попали 7 ложных файлов с `(modified)` из git uncommitted:
- `adv` (binary), `cmd/adv/main.go`, `ADV-T036_...md`, `internal/plan/findings/updater.go`, `internal/plan/freeze/evaluator.go`, `internal/plan/freeze/freeze_test.go`, `internal/plan/state/store_test.go`

Реально изменённый файл (`~/.claude/settings.json`) — помечен `(read)` вместо `(modified)` (SA-T058 пересечение).

**Fix:** 7 phantom artifacts удалены из export. settings.json → `(read, modified)`.

## Связь

SA-T075 (diffs-from-uncommitted-prior-sessions) — один фикс решит оба бага.
