**Дата:** 2026-04-09
**Статус:** open
**Sev:** HIGH

# SA-T075 — Diffs: захват uncommitted изменений из предыдущих сессий

## Проблема

Секция `## Diffs` содержит git diffs **всех** uncommitted файлов, а не только файлов, изменённых в текущей сессии.

## Воспроизведение

Сессия `33b531d7` модифицировала только `T152_s15_hidden_brand_bug.md`. В diffs попали ещё 4 файла:
- `.claude/commands/codereview-local.md` — изменён в предыдущей сессии
- `.claude/settings.local.json` — изменён в предыдущей сессии
- `T151_s15_series_popup_from_selection.md` — изменён в предыдущей сессии
- `T153_s15_installation_visualization.md` — изменён в предыдущей сессии
- `e2e/report/index.html` — изменён в предыдущей сессии

## Root cause

`build_diffs()` использует `git diff HEAD` (или `git diff`) — это показывает ВСЕ uncommitted изменения, включая те, что были сделаны до начала текущей сессии.

## Рекомендация

Вариант A (рекомендуемый): Записывать `base_commit` при старте сессии (первый message timestamp → `git log --before=<timestamp> -1 --format=%H`). Затем делать `git diff <base_commit>` — покажет только изменения, сделанные после начала сессии.

Вариант B: Пересечь список файлов из diffs с artifacts (modified) из парсера — оставить только те, что реально трогались в текущей сессии.

Вариант C: Если `--tool-ids` передан — использовать Edit/Write tool calls для определения списка изменённых файлов, и брать diffs только для них.

### Новое воспроизведение (2026-04-09, session bd314e97)

Сессия в проекте autodev-v2 модифицировала только 3 файла:
- `ADV-T045_s04_parity_and_integration_tests.md` (appended review findings)
- `~/.claude/commands/codereview.md` (added B7 items 10-11)
- `~/.claude/commands/smoketest.md` (added category J, flakiness checks)

В diffs попали 6 ложных файлов (все — uncommitted changes из предыдущих сессий):
- `docs/2. specifications/ADV-S04_...` — modified in prior session
- `docs/2. specifications/ADV-S05_...` — modified in prior session
- `docs/3. tasks/.../ADV-T028_...` — deleted in prior session
- `docs/3. tasks/.../ADV-T049_...` — deleted in prior session
- `docs/ADV-CHANGELOG.md` — modified in prior session
- `internal/executor/executor_test.go` — modified in prior session

Также попали в `session_artifacts` SQLite таблицу как `modified`/`deleted`.

### Воспроизведение #3 (2026-04-09, session 8f1a8c41, sproektirui)

Сессия T152 (hidden brand bug fix) модифицировала 4 файла:
- `useAppStore.js` (added cleanup in loadCatalogData)
- `DeviceCalculator.jsx` (removed T152 useEffect)
- `T152_s15_hidden_brand_bug.md` (added code review + fix verification)
- `codereview.md` (added checks #11, #12)

В diffs попали 6 ложных файлов (все uncommitted из T151/T153 сессий):
- `codereview-local.md` — modified in T149 session
- `settings.local.json` — background
- `T151_s15_series_popup_from_selection.md` — modified in T151 session
- `T153_s15_installation_visualization.md` — modified in T153 session
- `e2e/report/index.html` — background
- `WindowVisualization.jsx` — modified in T153 session

**Fix:** Manually removed incorrect diffs from export. Set `manually_reviewed = 1`.

Исправлено вручную в export .md + SQLite через `/verify-archive`.

### Воспроизведение #4 (2026-04-09, session 29ff92a9, autodev-v2)

Read-only сессия (0 Edit/Write): `/intro` + анализ T045 review iterations. В diffs попали 15 phantom файлов (2200 строк), включая binary `adv` patch (450 строк). Export раздулся до 65K tokens (2531→316 строк после фикса). Все 15 — uncommitted changes от предыдущих сессий на ветке `codex/pipeline-hardening-stageb-finalize`.

**Fix:** Удалена вся Diffs секция (0 реальных diffs), 15 phantom artifacts из SQLite, `manually_reviewed = 1`.

### Воспроизведение #5 (2026-04-11, session a1d889f9, autodev-v2)

`/codereview t052` (третий проход) — реально изменён только 1 файл: appended секция `## Code Review — 2026-04-11 (третий проход, придирчивый post-fix)` в конец `ADV-T052_s04_runner_state_durability.md`.

В diffs попали:
- **T052 task md** — diff capture захватил весь `git diff HEAD` (`@@ -98,3 +98,454`), включая 5 предыдущих разделов (`Code Review — 09:24`, `Smoke Test`, `Повторное ревью`, `Fix`, `Post-fix smoke`) из prior sessions, а не только session-scoped append
- **ADV-T033_s06_cli_plan_context_runner.md** — **полностью фантом**, файл НЕ трогался в сессии вообще (1 full diff block на ~160 строк); uncommitted от предыдущей сессии на ветке `codex/pipeline-hardening-stageb-finalize`

**Fix:** T033 diff block удалён из export полностью; T052 diff оставлен с verify-archive NOTE о том, что это `git diff HEAD` snapshot, а не session-scoped. `session_artifacts` запись ADV-T033 удалена из SQLite.

Таким образом этот bug **стабильно воспроизводится** на любой сессии, работающей в ветке с uncommitted чужими изменениями — даже при явном указании `--tool-ids`. Подтверждает приоритет варианта A (base_commit snapshot на старте сессии) — варианты B/C не спасают, т.к. в T052 реальный файл ВСЁ РАВНО попадает с контаминированным diff'ом, просто список файлов становится точнее.

### Воспроизведение #5 (2026-04-11, session fa809fcb, autodev-v2)

Сессия `/fix T045` модифицировала 2 файла:
- `ADV-T045_...md` (обновление статусов N1/N11 → FIXED, добавление Fix Verification block)
- `tests/integration/adv_native_parity_test.go` (sync.Once shared build, timeout bump 10s→60s)

В diffs попали 6 ложных diff-блоков из **предыдущей T034 сессии** (uncommitted на той же ветке):
- `PROMPTS/plan_spec_critic.md` — T034 fix
- `cmd/adv/main.go` — T034 fix
- `cmd/adv/plan_test.go` — T034 fix
- `docs/.../ADV-T034_...md` — T034 code review sections
- `internal/plan/findings/findings_test.go` — T034 fix
- `internal/plan/findings/writer.go` — T034 fix

Итого: 6 из 8 diff-блоков были чужие. 519 строк удалено при ручной верификации.

### Воспроизведение #6 (2026-04-12, session a8e931c1, autodev-v2)

Сессия `/intro` + создание 2 gate-задач (T055, T056) + 2× Edit HANDOFF. Реально изменены 3 файла:
- `docs/ADV-HANDOFF.md` (2 Edit)
- `docs/3. tasks/.../ADV-T055_...md` (Write, created)
- `docs/3. tasks/.../ADV-T056_...md` (Write, created)

В diffs попали 4 ложных diff-блока из **T034 сессии** (uncommitted на той же ветке):
- `PROMPTS/plan_spec_critic.md` — T034 fix
- `cmd/adv/main.go` — T034 fix
- `cmd/adv/plan_test.go` — T034 fix
- `docs/.../ADV-T045_...md` — T045 review appendix

Реальные diffs (HANDOFF edits, T055/T056 creates) **отсутствуют** — вообще не попали в export.

### Воспроизведение #7 (2026-04-12, session 591c2ded, autodev-v2)

Сессия `/codereview T045` — read-only анализ integration tests + 1 append в task file. Реально изменён 1 файл:
- `ADV-T045_...md` (append Code Review section)

В diffs попали 7 ложных diff-блоков (930 строк!) из **T034 сессии** (uncommitted на ветке `codex/pipeline-hardening-stageb-finalize`):
- `ADV-T034_s06_spec_critic_findings.md` — T034 code review
- `cmd/adv/main.go` — T034 fix (R2 --findings bypass)
- `internal/plan/findings/writer.go` — T034 fix (R1 sanitizer)
- `PROMPTS/plan_spec_critic.md` — T034 prompt fix
- `internal/plan/findings/findings_test.go` — T034 tests
- `cmd/adv/plan_test.go` — T034 tests
- `docs/ADV-HANDOFF.md` — phantom (prior session)

Также попал T045 task file diff, но он содержал ВСЕ uncommitted изменения (от 3+ предыдущих сессий), а не только session-scoped append.

**Fix:** Все 7 foreign diff-блоков удалены, заменены на session-scoped описание. `manually_reviewed = 1`.

### Воспроизведение #8 (2026-04-12, session 7eea8025, autodev-v2)

Сессия `/codereview T034` — анализ кода T034 (spec critic + findings) + 3 Edit в task file (append code review section + correction). Реально изменён 1 файл:
- `ADV-T034_s06_spec_critic_findings.md` (3× Edit: append Code Review, append correction)

В diffs попали 7 ложных diff-блоков (~600 строк) из **T045/T034 предыдущих сессий** (uncommitted на ветке `codex/pipeline-hardening-stageb-finalize`):
- `ADV-T045_s04_parity_and_integration_tests.md` — T045 prior session (254 строки)
- `PROMPTS/plan_spec_critic.md` — T034 prior fix session
- `cmd/adv/main.go` — T034 prior fix session
- `cmd/adv/plan_test.go` — T034 prior fix session
- `docs/ADV-HANDOFF.md` — prior session
- `internal/plan/findings/findings_test.go` — T034 prior fix session
- `internal/plan/findings/writer.go` — T034 prior fix session

**Fix:** Все 7 phantom diff-блоков удалены из export, оставлен только T034 task file diff. Phantom `modified` artifacts удалены из SQLite, заменены на `read`. `manually_reviewed = 1`.

### Воспроизведение #9 (2026-04-12, session 3e64f00c, autodev-v2)

Сессия `/smoketest T034` — реально изменён 1 файл: `ADV-T034_...md` (appended Smoke Test секция, ~80 строк).

В diffs попали 3 ложных diff-блока из **предыдущих сессий** (uncommitted на ветке):
- `cmd/adv/plan_test.go` — T034 prior fix session
- `docs/.../ADV-T045_...md` — T045 prior review session
- `tests/integration/adv_native_parity_test.go` — T045 prior fix session

Также T034 task file diff содержит ~300 строк из prior sessions (Code Review, Smoke Test 2026-04-11) — only last ~80 lines are from this session.

**Fix:** 3 phantom diff-блока удалены; note добавлен о mixed-session T034 diff. `manually_reviewed = 1`.

### Воспроизведение #5 (2026-04-12, session 9925b288, autodev-v2)

Сессия `/fix T045` + `/accept T045` модифицировала 6 файлов (integration tests, mock_executor, HANDOFF, CHANGELOG, S04 spec, T045 task file). Первоначальная архивация через `archive-current` включила в diffs ВСЕ uncommitted, в т.ч. 4 файла из предыдущей T034 сессии (PROMPTS/plan_spec_critic.md, cmd/adv/main.go, cmd/adv/plan_test.go, ADV-T034 task file) + пара файлов из ещё более ранних сессий (findings_test.go, writer.go).

**Особенность:** из-за SA-T085 (manually_reviewed guard) re-archive не перезаписал export — данные остались от ручной правки T034. Потребовалась ручная правка export .md для добавления T045 diffs.

### Воспроизведение #10 (2026-04-12, session dee157dd, autodev-v2)

Сессия: код-ревью gate-tasks T055/T056 + правки T055/T056 через Edit tool. Реально изменены 2 файла (T055 и T056 — оба untracked `??`). Парсер захватил diffs из **всех uncommitted файлов** на ветке `codex/pipeline-hardening-stageb-finalize`:
- `PROMPTS/plan_spec_critic.md` — T034 fix
- `cmd/adv/main.go` — T034 fix
- `cmd/adv/plan_test.go` — T034 fix
- `docs/2. specifications/ADV-S04_...` — modified in prior session
- `docs/2. specifications/ADV-S06_...` — modified in prior session
- `docs/ADV-CHANGELOG.md` — modified in prior session
- `docs/ADV-HANDOFF.md` — modified in prior session
- `internal/plan/findings/findings_test.go` — T034 fix
- `internal/plan/findings/writer.go` — T034 fix
- `internal/testutils/mock_executor.go` — T045 fix
- `tests/integration/adv_native_parity_test.go` — T045 fix

Также: T055/T056 — untracked файлы — **не попали** в git diff HEAD вообще (правильное поведение git, но export пуст по реальным правкам).

**Особенности:**
1. Реально изменённые файлы (T055, T056) — untracked, поэтому `git diff HEAD` их не показывает
2. 15 contaminated artifacts в SQLite из git status вместо session-scoped
3. Transcript section — cross-session contamination (SA-T084)

**Fix:** Export полностью переписан: Diffs заменён на session-specific описание Edit-правок (не git diff). 15 artifacts заменены на 8 корректных. Tasks: добавлены T055/T056. `manually_reviewed = 1`.

### Воспроизведение #11 (2026-04-12, session 088d7e4a, autodev-v2)

Read-only сессия (0 Edit/Write): `/smoketest T057` → отклонено как рефакторинг. В diffs попали **19 phantom diff-блоков** (~3000 строк) — все uncommitted changes от предыдущих сессий (T034, T045) на ветке `codex/pipeline-hardening-stageb-finalize`. Также 19 phantom artifacts с `(modified)`/`(deleted)` в SQLite.

**Fix:** Вся Diffs секция заменена на `_No file changes in this session_`, 19 phantom artifacts удалены из SQLite, заменены на 2 корректных `read`. Tasks: 5 ложных удалены (SA-T074).

### Воспроизведение #12 (2026-04-13, session 852dae4d, autodev-v2)

Сессия `/smoketest T026` — реально изменён 1 файл: `ADV-T026_s05_task_dag_scheduler.md` (append Smoke Test секция). Также создан и удалён temp файл `smoketest_t026_test.go`.

В diffs попали **12 ложных diff-блоков** (~1900 строк) из **предыдущих сессий** (uncommitted на ветке `codex/pipeline-hardening-stageb-finalize`):
- `adv` (binary — 450 строк binary patch noise!)
- `cmd/adv/main.go` — prior session
- `docs/2. specifications/ADV-S05_...` — prior session
- `docs/2. specifications/ADV-S06_...` — prior session
- `docs/3. tasks/.../ADV-T046_...` — deleted in prior session
- `docs/3. tasks/.../ADV-T035_...` — deleted in prior session
- `docs/3. tasks/.../ADV-T055_...` — prior session
- `docs/3. tasks/.../ADV-T056_...` — prior session
- `docs/ADV-CHANGELOG.md` — prior session
- `docs/ADV-architecture.md` — prior session
- `internal/plan/findings/findings_test.go` — prior session
- `internal/worktree/worktree_test.go` — prior session

Также 12 phantom `(modified)`/`(deleted)` artifacts в SQLite.

**Fix:** 12 phantom diff-блоков удалены из export (~1900 строк). 12 phantom artifacts удалены из SQLite. `manually_reviewed = 1`.

### Воспроизведение #13 (2026-04-13, session 5cf74de4, autodev-v2)

Read-only code review сессия (`/codereview-free T029`): 0 Edit/Write на repo-файлы. Единственные Write/Edit — memory-файлы вне repo (`~/.claude/projects/.../memory/`).

В diffs попали **10 ложных diff-блоков** (~1650 строк), включая binary `adv` patch (~450 строк). Все — uncommitted changes от предыдущих сессий на ветке `codex/pipeline-hardening-stageb-finalize`:
- `adv` (binary patch — 450 строк noise)
- `cmd/adv/main_test.go` — prior session
- `docs/2. specifications/ADV-S05_...` — prior session
- `docs/3. tasks/.../ADV-T026_...` — deleted in prior session
- `docs/3. tasks/.../ADV-T027_...` — deleted in prior session
- `docs/3. tasks/.../ADV-T031_...` — prior session
- `docs/ADV-CHANGELOG.md` — prior session
- `docs/ADV-HANDOFF.md` — prior session
- `internal/state/state_test.go` — prior session
- `internal/worktree/worktree.go` — prior session

Также 10 phantom `(modified)`/`(deleted)` artifacts.

**Fix:** Вся Diffs секция заменена на `_No repository files were modified in this session._`. 10 phantom artifacts удалены из export. Open Issues исправлены (SA-T080 prec #3). Events исправлены (SA-T059 prec #4).

### Воспроизведение #14 (2026-04-13, session `cde4f5f3`, autodev-v2)

Исследовательская сессия: deep research "бирж труда" для AI-агентов (WebSearch ×5, Write ×1). Единственный созданный файл: `docs/5. Unsorted/agent_labor_marketplaces_research.md`.

В diffs попали **20 phantom diff-блоков** (~3300 строк!), включая binary `adv` patch (~450 строк). Все — uncommitted changes от предыдущих сессий на ветке `codex/pipeline-hardening-stageb-finalize`:
- `adv` (binary patch), `cmd/adv/main.go`, `cmd/adv/main_test.go`
- `docs/2. specifications/ADV-S05_...` (modified)
- `docs/3. tasks/.../ADV-T026_...`, `ADV-T027_...` (deleted)
- `docs/3. tasks/.../ADV-T029_...`, `ADV-T031_...` (modified)
- `docs/ADV-CHANGELOG.md`, `docs/ADV-HANDOFF.md` (modified)
- `internal/runner/run.go`, `runner.go` (modified)
- `internal/scheduler/interfaces.go`, `task_dag_scheduler.go`, `task_dag_scheduler_test.go`, `task_worker.go` (modified)
- `internal/state/state.go`, `state_test.go` (modified)
- `internal/worktree/worktree.go` (modified)
- `tests/integration/adv_native_parity_test.go` (modified)

Export раздулся до 3840 строк (вместо ~520 после фикса). Также 20 phantom artifacts в SQLite.

**Fix:** 20 phantom diff-блоков удалены из export (3300 строк). 20 phantom artifacts удалены из SQLite. `manually_reviewed = 1`.

### Воспроизведение #15 (2026-04-13, session `add435f7`, autodev-v2)

Сессия: deep research по продвижению AutoDev (WebSearch ×8, WebFetch ×3, Edit ×3). Реально изменены 2 файла:
- `docs/ADV-HANDOFF.md` (Read + Edit — обновление пункта про биржи)
- `docs/5. Unsorted/agent_labor_marketplaces_research.md` (Read + 2× Edit — добавление секции GTM-стратегии + sources)

В diffs попали **17 phantom diff-блоков** (~3400 строк), включая binary `adv` patch. Все — uncommitted changes от предыдущих сессий на ветке `codex/pipeline-hardening-stageb-finalize`:
- `adv` (binary), `cmd/adv/main.go`, `cmd/adv/main_test.go`
- `docs/2. specifications/ADV-S05_...`, `docs/ADV-CHANGELOG.md`
- `docs/3. tasks/.../ADV-T026_...` (deleted), `ADV-T027_...` (deleted), `ADV-T029_...`, `ADV-T031_...`
- `internal/runner/run.go`, `runner.go`
- `internal/scheduler/interfaces.go`, `task_dag_scheduler.go`, `task_dag_scheduler_test.go`, `task_worker.go`
- `internal/state/state.go`, `state_test.go`, `internal/worktree/worktree.go`
- `tests/integration/adv_native_parity_test.go`

Также 17 phantom `(modified)`/`(deleted)` artifacts. HANDOFF diff содержит чужие изменения (T026/T027 done, T031 update, Planning→execution, Provider-agnostic) наряду с session-scoped правкой.

**Fix:** Artifacts в export заменены на 2 корректных + NOTE. Tags/Events исправлены (удалены meta-skills, добавлены domain:strategy, skill:web-research). Diffs NOT cleaned (17 phantom блоков остались — слишком много для ручной чистки; ожидание SA-T075 fix в парсере).

### Воспроизведение #16 (2026-04-13, session `2ab24fa4`, sproektirui)

Сессия: сортировка карточек Trello (T150, T148, T147) + cache-bust fix в `admin.py` + создание memory файла. Реально изменён 1 repo-файл: `teplofort1-app/backend/app/routers/admin.py`.

В diffs попали **все** diffs от ПРЕДЫДУЩЕЙ сессии в том же JSONL (T149/T153):
- `DeviceCalculator.jsx` — T149 CSS tooltip fix (prior session)
- `WindowVisualization.jsx` — T153 legend removal (prior session)
- `S15_sprint4.md` — T153 spec update (prior session)
- `CHANGELOG.md` — T149/T153 entries (prior session)

**Особенность:** export содержал полностью чужой summary, tags, tasks, events и artifacts — всё от предыдущей сессии T149/T153 вместо текущей. Причина: JSONL `2ab24fa4` содержит обе сессии; `archive-current` перезаписал данные текущей сессии данными предыдущей (SA-T072 / SA-T073).

**Новая находка:** в отличие от autodev-v2 (где phantom diffs из git uncommitted), здесь **все phantom diffs — корректные git diffs от предыдущей сессии**, записанные в тот же JSONL. Парсер не разделяет сессии внутри одного JSONL-файла.

**Fix:** export и SQLite полностью переписаны вручную через verify-archive. Summary, tags, events, tasks, artifacts, diffs — всё заменено.

### Воспроизведение #17 (2026-04-14, session `21dee077`, autodev-v2)

Сессия `/codereview T036` — реально изменён 1 файл: `ADV-T036_s06_freeze_evaluation.md` (append Code Review section через Edit tool).

В diffs попали **34 phantom diff-блока** (~4700 строк!), включая binary `adv` patch (~450 строк). Все — uncommitted changes от предыдущих сессий на ветке `codex/pipeline-hardening-stageb-finalize`:
- `adv` (binary), `cmd/adv/main.go`, `cmd/adv/main_test.go`
- `docs/2. specifications/ADV-S05_...` + множество task files из S05/S07/S08
- `docs/ADV-CHANGELOG.md`, `docs/ADV-HANDOFF.md`
- `internal/dag/`, `internal/plan/freeze/evaluator.go`, `internal/runner/`, `internal/scheduler/`, `internal/state/`, `internal/worktree/`
- `tests/integration/adv_native_parity_test.go`

Export раздулся до 4776 строк (вместо ~192 после фикса). Также 34 phantom artifacts в SQLite.

**Дополнительный баг:** реальный diff T036 task file (наш Edit) **НЕ попал** в export — файл уже был в git status (uncommitted from prior T036 implementation session), но diff показывал ВСЁ, включая prior changes. Скрипт включил `evaluator.go` diff (от T036 implementation session, не от текущего code review), но НЕ включил T036 task file diff.

**Fix:** Все 34 phantom diff-блоки удалены. Заменены session-scoped diff из `git diff -- ADV-T036_...md`. 34 phantom artifacts заменены на 11 корректных. Events/Tags исправлены. `tool_call_count` 4→25.

**Повторная контаминация (2026-04-14, --force re-archive):** `archive-current --force` на ту же сессию снова записал 81 diff-секцию и 42 артефакта (35 phantom). Баг воспроизводится стабильно: каждый `--force` re-archive восстанавливает контаминацию, т.к. `build_diffs()` не имеет session scope.

**Fix #2:** Повторная ручная чистка: 35 phantom artifacts, 76 phantom diffs удалены. `code_reviewed` event добавлен. Tasks dedup (T036 → ADV-T036, T042 phantom удалён).

### Воспроизведение #18 (2026-04-14, session `c60ad134`, autodev-v2)

Сессия: исследование open-source инструментов + настройка golangci-lint hooks в `~/.claude/settings.json`. Единственный изменённый файл — `~/.claude/settings.json` (вне git repo). 0 Edit/Write на repo-файлы.

В diffs попали **все uncommitted changes** из ветки `codex/pipeline-hardening-stageb-finalize`, включая binary `adv` patch. Export раздулся до 1291 строк (вместо ~502 после фикса).

Также 7 ложных artifacts с `(modified)`:
- `adv`, `cmd/adv/main.go`, `ADV-T036_...md`, `internal/plan/findings/updater.go`, `internal/plan/freeze/evaluator.go`, `internal/plan/freeze/freeze_test.go`, `internal/plan/state/store_test.go`

Ни один из этих файлов не трогался в сессии. Реальный изменённый файл (`~/.claude/settings.json`) помечен как `(read)` вместо `(modified)` — пересечение с SA-T058 (artifacts вне project_path) + SA-T076 (action classification).

**Fix:** 7 phantom artifacts удалены, settings.json → `(read, modified)`. Diffs заменены на session-scoped diff из Edit tool call. `manually_reviewed` не установлен (SQLite не имеет этого поля для artifacts).

## Связь

Частично связан с SA-T052 (diffs-artifacts-git-contamination).
Связан с SA-T076 (artifacts-from-git-uncommitted) — одна и та же root cause (`git diff HEAD` вместо session-scoped).
