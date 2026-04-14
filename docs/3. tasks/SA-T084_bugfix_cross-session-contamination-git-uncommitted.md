# SA-T084 — Cross-session contamination from git uncommitted changes

**Дата:** 2026-04-12
**Severity:** HIGH
**Обнаружено:** verify-archive на сессии `9925b288` (autodev-v2, T034 code review)

## Описание

При архивации read-only сессии (только ревью кода, един��твенный Edit в один файл) с��рипт захватил:
- **7 «modified» артефактов** из 1 реально изменённого — остальные 6 были uncommitted diffs из предыдущих сессий
- **Полные git diffs** всех uncommitted файлов, вк��ючая `tests/integration/adv_native_parity_test.go` (вообще из другой задачи T045)
- **Tasks:** T042, T045 вместо T034 — задачи вероятно из другой с��ссии в том же JSONL или из git status
- **Open Issues:** текст "T045 готова к accept" из контента прочитанного файла, не из этой сессии
- **Skills:** `fix`, `intro` вместо `codereview-free` — вероятно из system-reminder skill list или из другой сессии
- **Events:** `spec_read` — false positive

## Root Cause (предположительно)

1. **Diffs:** скрипт берёт `git diff HEAD` для всех файл��в в артефактах, не различая «файл модифицирован в этой сессии» vs «файл уже был modified до сессии». Любой Read на uncommitted файл помечается как «modified» артефакт.

2. **Tasks/Open Issues/Skills:** при messages=4 (JSONL с��держит только 50 строк, фильтрация по tool-ids захватила мало), парсер вероятно извлекает metadata из контента system-reminder'ов или прочитанных файлов, а не из реальных действий пользователя/ассистента.

3. **Messages=4:** tool-ids фильтр слишком агрессивный — часть tool_call_ids не попадает в JSONL (Claude Code может не записывать все tool_use в JSONL, или формат id отличается).

## Воспроизведение

1. Иметь несколько uncommitted файлов в рабочем дереве (от предыдущих сессий)
2. Начать новую сессию, прочитать эти файлы (Read tool), изменить только один
3. Запустить `/archive-session`
4. Проверить: все прочитанные файлы будут помечены как `modified`, их diffs включены

## Рекомендация

### Для diffs/artifacts (HIGH):
- Различать `session_edit` (файл изменён через Edit/Write в этой сессии) vs `pre_existing_uncommitted` (файл уже был uncommitted до сессии, только прочитан)
- При наличии tool-ids: файл считать modified только если есть Edit/Write tool_call на этот ��айл в границах сессии
- При отсутствии tool-ids: сравнить mtime файла с началом сессии, или проверить git log за время сессии

### Для tasks (MEDIUM):
- Не извлекать task IDs из с��держимого прочитанных файлов (HANDOFF, task files) — только из explicit tool calls и user/assistant messages
- Task из `Read(ADV-HANDOFF.md)` результата — это контекст, не «задача сессии»

### Для skills (MEDIUM):
- Не извлекать skill tags из system-reminder списка доступных скиллов
- Skill tag = только реально вызванный через Skill tool (проверять `type: tool_use, name: Skill`)

### Для messages count (MEDIUM):
- Если tool-ids фильтр даёт < 10 messages — fallback н�� sessionId-based фильтр
- Логировать предупреждение при messages < 10

### Воспроизведение 2 (2026-04-12, session `4e419074`, autodev-v2, T057 review)

Сессия: review + fix T057 задачи (3 файла modified: HANDOFF, T057, S04 spec). Парсер захватил **17 артефактов** вместо 6 (3 modified + 3 read). Лишние 11:
- `PROMPTS/plan_spec_critic.md` (modified) — из предыдущей сессии T034
- `cmd/adv/main.go` (modified) — из T034
- `cmd/adv/plan_test.go` (modified) — из T034
- `docs/2. specifications/ADV-S06_*` (modified) — из T034
- `ADV-T045_*` (deleted) — из accept T045
- `ADV-T034_*` (deleted) — из accept T034
- `docs/ADV-CHANGELOG.md` (modified) — из T034/T045
- `internal/plan/findings/*` (modified) — из T034
- `internal/testutils/mock_executor.go` (modified) — из T045
- `tests/integration/adv_native_parity_test.go` (modified) — из T045

Все 11 — uncommitted changes от предыдущих сессий (T034, T045). git_head diffs включены в export (~1250 строк phantom diffs). Ручной fix: удалены из export + SQLite.

Паттерн идентичен `9925b288`. Отличие: session имела достаточно messages (15), tool-ids не использовались — так что root cause здесь чисто в artifact/diff extraction, не в JSONL boundary.

### Воспроизведение 3 (2026-04-12, session `dee157dd`, autodev-v2, T055/T056 gate review)

Сессия: придирчивый код-ревью + правки gate-tasks T055/T056. JSONL `dee157dd` содержит cross-session contamination — tool_call_ids из предыдущих сессий (T057 creation, prior gate review). Парсер захватил:
- **15 artifacts** вместо 8 реальных — 7 phantom из git status M/D (T034/T045 prior sessions)
- **Diffs** из git diff HEAD — все от prior sessions (T055/T056 untracked, не попали в git diff)
- **Tasks:** только T057 (mentioned) — T055/T056 не извлечены (Edit tool на untracked файлы не детектируется)
- **Transcript:** содержит записи из предыдущих сессий в том же JSONL, sessionId-фильтр не отделяет

**Отличие от Воспроизведения 1:** tool-ids не передавались (сессия слишком длинная), sessionId-фильтр — единственная boundary. Парсер захватывает messages из ВСЕХ сессий в JSONL с одинаковым sessionId.

**Fix:** export полностью переписан вручную через verify-archive. SQLite обновлён: artifacts, tasks, summary, tags.

### Воспроизведение 4 (2026-04-13, session `f553b46c`, autodev-v2, T055/T056 gate review Round 4)

Сессия: /intro → ревью gate-tasks T055/T056 Round 4 → запись результата в md → /archive-session. Единственный Write: `docs/5. Unsorted/ADV-T055-T056_gate_review_round4_2026-04-13.md`.

Парсер захватил:
- **30 artifacts** вместо 18 реальных — 12 phantom:
  - 6 `(created)`: scheduler/config.go, interfaces.go, task_worker.go, task_dag_scheduler.go, runner/run.go, task_dag_scheduler_test.go — всё из предыдущей сессии (T026 implementation)
  - 6 `(read)` из чужой сессии: scheduler.go, runner/runner.go, pipeline.go, state.go, advlog/logger.go, metrics.go, dag.go, handoff_sync.go, scheduler_test.go
  - 10 `(modified/deleted)` из git status: adv, S06 spec, T046, T035, T055, T056, CHANGELOG, architecture, findings_test, worktree_test — все uncommitted changes от prior sessions
- **Diffs:** ~3700 строк phantom diffs (полные файлы scheduler/*.go + git diff HEAD для всех uncommitted)
- **Tags:** `skill: next` вместо `skill: intro` — /next был первым сообщением в JSONL (из другой сессии), парсер захватил его
- **Events:** `tests_run` false positive — тесты не запускались; missing `code_reviewed`
- **Tasks:** пусто — T055/T056 не извлечены (только Read, не Edit)

**Root cause:** тот же что у Воспр. 1-3. JSONL содержит messages из предыдущей сессии (T026 implementation), sessionId-фильтр не разделяет. Artifact extraction из git status/diff добавляет phantom entries.

**Новая находка:** `skill: next` tag — парсер извлёк из `<command-name>/next</command-name>` в transcript первого сообщения JSONL (из другой сессии). Реальная сессия начиналась с `/intro`.

**Fix:** export и SQLite исправлены вручную (verify-archive): artifacts 30→18, diffs 3700→15 строк, tags/events/tasks corrected.

### Воспроизведение 4 (2026-04-12, session `69d11152`, autodev-v2, T046 codereview)

Сессия: codereview T046 (WorktreeManager.Apply refactor). 1 файл изменён (Edit на task file T046). Парсер захватил:
- **22 artifacts** вместо 9 реальных (1 modified + 8 read) — 13 phantom из git status M/D (T034/T045 prior sessions)
- **21 git_head diffs** (~2500 строк) — все от prior sessions. Единственный корректный diff: T046 task file (+53 строки code review)
- **Tasks:** T001, T024, T032, T042, T048 — false positives из содержимого HANDOFF (Read). Только T046 реальная
- **Skill:** `archive-session` вместо `codereview` — SA-T082
- **Events:** только `session_archived` — пропущен `code_reviewed`, `tests_ran`
- **Tool calls:** 0 вместо 17 — SA-T079

**Fix:** export переписан (3346→918 строк). SQLite обновлён: artifacts, tasks, tags, events, tool_call_count.

### Воспроизведение 5 (2026-04-12, session `898fa735`, autodev-v2, T057 third code review)

Сессия: третье независимое код-ревью T057 (extract finalize methods). 1 файл изменён (Edit на T057 task file). Парсер захватил при первой экстракции:
- **21 artifact** вместо 11 реальных (1 modified + 10 read) — 10 phantom из git status M/D (T034/T045 prior sessions)
- Phantom artifacts: `PROMPTS/plan_spec_critic.md`, `cmd/adv/plan_test.go`, specs S04/S06/S07, T045/T034 (deleted), CHANGELOG, HANDOFF, mock_executor, integration tests
- При re-extraction (повторный запуск archive-current) summary/messages/tool_calls были перезаписаны данными другой сессии ("T055/T056 gate review", messages=15, tool_calls=0)
- **Tasks:** `T057` — корректно, но дубль `ADV-T057` + `T057`
- **Events:** `tests_run`, `session_archived` — пропущен `code_reviewed` (SA-T083)
- **Tags:** `domain: docs` вместо `domain: go` — неточная классификация по типу edited файла (.md) а не по работе сессии (чтение Go кода)

**Дополнительная проблема:** re-extraction destroyed curated data. Повторный запуск `archive-current` перезаписал ранее правильный summary некорректным (из контекста другой сессии в том же JSONL). Это SA-T085.

**Fix:** export и SQLite исправлены вручную: summary, tags (domain: go, pipeline; удалён archive-session skill), events (добавлен code_reviewed), tasks (дедуплицирован), artifacts (удалены 10 phantom).

### Воспроизведение 6 (2026-04-13, session `e2b6c4f6`, autodev-v2, T031 gate review)

Сессия: придирчивый код-ревью gate-task T031 (S05 integration tests) → самокритика → правки задачи → archive + verify. Изменён 1 файл (7 Edit на T031 task doc). Парсер захватил:
- **5 phantom artifacts** (modified): `ADV-HANDOFF.md`, `task_dag_scheduler.go`, `task_worker.go`, `state.go`, `ADV-T026_s05_task_dag_scheduler.md` — все uncommitted changes от предыдущих сессий (T026 implementation, T045/T034 accept)
- **5 phantom diffs** (~400 строк): полные git diffs для тех же 5 файлов. Реальный diff — только T031 task doc
- **Tasks:** `-T030` — parsing artifact, вероятно из grep output где `-` перед номером задачи интерпретирован как часть ID. Также дублирование `T031` / `ADV-T031`
- **Tags:** missing `skill: code-review` — реально проводился code-review, но skill tag не извлечён
- **Events:** missing `task_read`, `code_read`, `task_updated` — реально читались task docs и code файлы, обновлялась задача

**Root cause:** идентичен Воспр. 1-5. Git status содержал uncommitted changes от prior sessions; парсер не различает session-specific edits от pre-existing uncommitted.

**Новая находка:** `-T030` parsing bug — парсер извлекает task IDs regex'ом и захватывает `-T030` из контекста типа `grep -T030` или markdown list item `- T030`. Рекомендация: strip leading `-` при извлечении task IDs, или требовать prefix `ADV-` / `T` без leading punctuation.

**Fix:** export и SQLite исправлены вручную: artifacts (удалены 5 phantom), diffs (удалены 5 phantom), tasks (удалён `-T030`, дедуплицирован T031), tags (добавлен `skill: code-review`), events (добавлены 3 missing), transcript (восстановлено первое USER сообщение после неудачного удаления phantom diffs).

### Воспроизведение 7 (2026-04-13, session `169a9992`, autodev-v2, T029 audit fix)

Сессия: /intro → /fix T029 → 6 audit findings fixed (3 HIGH, 3 MEDIUM) → archive + verify. 5 файлов изменено (Edit): task_worker.go, synced_handoff_sync.go, cmd/adv/main.go, synced_handoff_sync_test.go, T029 task doc. 3 файла только прочитаны (Read): HANDOFF, architecture, state.go.

Парсер захватил:
- **22 artifacts** вместо 8 реальных — 14 phantom из git status M/D/?? (T026/T027/T046 prior sessions):
  - `adv` (modified) — binary, pre-existing
  - `cmd/adv/main_test.go` (modified) — not touched this session
  - `docs/2. specifications/ADV-S05_*` (modified) — prior session
  - `docs/3. tasks/*/ADV-T026_*` (deleted) — moved to Done in prior session
  - `docs/3. tasks/*/ADV-T027_*` (deleted) — moved to Done in prior session
  - `docs/3. tasks/*/ADV-T031_*` (modified) — prior session
  - `docs/ADV-CHANGELOG.md` (modified) — prior session
  - `internal/runner/run.go`, `runner.go` (modified) — prior session
  - `internal/scheduler/interfaces.go`, `task_dag_scheduler.go`, `task_dag_scheduler_test.go` (modified) — prior session
  - `internal/state/state_test.go` (modified) — prior session
  - `internal/worktree/worktree.go` (modified) — prior session
  - `tests/integration/adv_native_parity_test.go` (modified) — prior session
- **Tasks:** `T042` false positive (from HANDOFF content), `T029` duplicate of `ADV-T029`
- **Diffs:** git_head diffs for task_worker.go and main.go include changes from prior sessions (CFR#1-3 fixes done before this session)

**Root cause:** identical to Reproductions 1-6. Git working tree had ~20 uncommitted files from T026/T027/T046 sessions.

**Fix:** export + SQLite corrected by verify-archive: artifacts 22→8, tasks 3→1, phantom diffs remain (git_head includes prior changes — would need synthetic diffs to isolate session-specific changes).

### Воспроизведение 8 (2026-04-13, session `2ab24fa4`, sproektirui, T149/T153 founder feedback fixes)

Сессия: /intro → сортировка карточек Trello → фикс T149 (CSS-тултип вместо HTML title) → фикс T153 (убрана легенда, белый радиатор) → деплой × 2 → обновление CHANGELOG + S15 спеки → archive.

4 файла изменены (Edit): `DeviceCalculator.jsx`, `WindowVisualization.jsx`, `CHANGELOG.md`, `S15_sprint4.md`.
2 файла прочитаны (Read): `HANDOFF.md`, `S15_sprint4.md`.

Парсер захватил:
- **Summary:** от ПРЕДЫДУЩЕЙ сессии ("перенесли 4 карточки... T150, T148, T147... cache-bust") — `--summary` аргумент проигнорирован (SA-T072). Реальный summary: "фикс T149 + T153 по фидбеку фаундера"
- **8 phantom artifacts** вместо 4 реальных modified:
  - `PrivacyPage.jsx` (modified) — uncommitted edit от предыдущей сессии, в этой сессии НЕ трогали
  - `e2e/report/index.html` (modified) — uncommitted от предыдущей сессии
  - 6× `e2e/screenshots/review/t153-*.png` (modified) — uncommitted от предыдущей сессии
- **Diffs:** полный diff `PrivacyPage.jsx` (~100 строк) + base64 Playwright report + бинарные PNG — всё phantom
- **Tasks:** пусто — T149 и T153 не извлечены (Edit tool calls не парсятся или task extraction не сработала)
- **Events:** `push_made` false positive — git push НЕ делался, деплой через `ssh heating-cloud`; `trello_read` missing
- **Tags:** `skill: intro` — ок, но missing `trello` (MCP tools использовались 5+ раз)

**Root cause:** идентичен Воспр. 1-7. Git working tree содержал uncommitted changes от предыдущих сессий (PrivacyPage, e2e). Плюс SA-T072: `--summary` аргумент не перезаписал существующий `summary_manual`.

**Новые находки:**
1. **MCP tool calls не создают skill tags** — 5+ вызовов `mcp__trello__*` не привели к tag `trello`
2. **SSH deploy не детектируется как event** — `deploy` event присутствует (видимо из `docker compose up` в bash), но `push_made` false positive (парсер видит `git pull origin dev` в SSH-команде и считает это push?)

**Fix:** export + SQLite полностью переписаны вручную через verify-archive.

### Воспроизведение 9 (2026-04-14, session `c1332233`, autodev-v2, fix T029 smoke/CR findings)

Сессия: /intro → /fix T029 → 6 findings fixed (5 HIGH, 1 MEDIUM) → archive + verify. 7 файлов изменено (Edit): dag.go, dag_test.go, task_dag_scheduler.go, task_worker.go, synced_handoff_sync.go, cmd/adv/main.go, T029 task doc. 4 файла только прочитаны (Read): HANDOFF, architecture, run.go, scheduler_test.go.

Парсер захватил:
- **38 artifacts** вместо 11 реальных — 27 phantom из git status M/D/?? (prior sessions T026/T027/T046/T035 etc.):
  - `adv` (modified) — binary, pre-existing
  - `cmd/adv/main_test.go` (modified) — not touched
  - 16× `docs/3. tasks/ADV-S0{6,7,8}_*` (modified/deleted) — all from prior sessions
  - `docs/2. specifications/ADV-S05_*` (modified) — prior session
  - `docs/ADV-CHANGELOG.md`, `internal/runner/runner.go`, `internal/state/state*.go`, `internal/worktree/worktree.go`, `tests/integration/*` — all prior sessions
- **32 diffs** вместо 7 — includes binary `adv` (useless), all uncommitted prior changes
- **Tasks:** `T001,T024,T032,T036,T042,T046,T048` — ALL false positives from HANDOFF/task file content. Real: only T029
- **Tags:** `skill: smoketest` — false positive from system-reminder skill list. Real: `fix`, `intro`
- **Events:** `spec_read` false positive — architecture.md was read, not a spec
- **Messages:** 2 instead of ~8 (JSONL boundary issue)
- **Tool calls:** 13 instead of ~40+

**Root cause:** identical to Reproductions 1-8. Binary `adv` in diffs is a new variant — no binary filter.

**New finding:** binary compiled Go executable (`adv`) included in diffs as base64 git binary patch (~5MB of useless data). Recommendation: filter out binary files from diff generation (check `git diff --name-only --diff-filter=d` and exclude files detected as binary by `file --mime`).

**Fix:** export + SQLite corrected by verify-archive: tasks 7→1, tags fixed (smoketest→fix/intro), events fixed (spec_read→architecture_read), artifacts 38→11.

## Связанные баги

- SA-T075 (diffs from uncommitted prior sessions) — частично перекрывается
- SA-T073 (cross-session contamination in single JSONL) — related root cause
- SA-T076 (artifacts from git uncommitted) — same class
