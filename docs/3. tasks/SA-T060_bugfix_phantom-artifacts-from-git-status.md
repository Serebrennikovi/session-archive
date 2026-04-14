**Дата:** 2026-04-08
**Статус:** draft

# SA-T060 — Phantom artifacts and diffs from git status

## Проблема

Файлы из `git status` (uncommitted changes from **previous** sessions) попадают в artifacts и diffs текущей сессии. Это засоряет архив ~10 ложными артефактами и может добавить мегабайты binary diffs (например, скомпилированный бинарник `adv`).

## Как воспроизвести

1. В проекте есть uncommitted changes от предыдущих сессий (например, `git status` показывает Modified `cmd/adv/main.go`, `internal/runner/runner.go`, deleted task files)
2. Текущая сессия редактирует **только** 3 файла (T049, T029, HANDOFF)
3. `archive-current` записывает в artifacts все файлы из `git diff HEAD` — включая 10 файлов, которые текущая сессия не трогала

## Прецедент

Session `ccc065da`: 12 корректных артефактов + 10 phantom (binary `adv`, `cmd/adv/main.go`, 4 deleted task files, `ADV-architecture.md`, `config.go`, `runner.go`, `T045`). Phantom diffs = ~1600 строк (из 2182 total), включая 450-строчный binary patch для `adv`.

## Root cause

`session_archive.py` использует `git diff HEAD` (или `git status`) для определения modified/deleted артефактов. Это показывает **все** uncommitted changes в worktree, не только изменения текущей сессии.

### Воспроизведение 2 (2026-04-13, session `410df60f`)

Сессия в autodev-v2 редактировала ТОЛЬКО 3 файла skill (`~/.claude/commands/codereview.md`, `smoketest.md`, `codereview-free.md`). В artifacts попали 20 файлов из `git status` (все uncommitted от prior sessions): binary `adv`, `cmd/adv/main.go`, `internal/runner/*`, `internal/scheduler/*`, deleted task files, etc. Diffs содержали ~3260 строк phantom binary + code diffs. Реальная работа сессии не была в artifacts вообще (skill files вне project_path, см. SA-T058).

## Рекомендуемый фикс

Два подхода (можно комбинировать):

**A) Filter by session tool calls:** Только файлы, которые фигурируют в `Edit`/`Write` tool calls текущей сессии, считать modified. Это уже частично работает для Read-артефактов (через JSONL parsing). Аналогично для diffs: генерировать synthetic diff только для файлов с Edit/Write tool calls.

**B) Snapshot-based diff:** Запомнить `git stash create` (или `git diff --stat`) в начале сессии, при архивации сравнить с текущим состоянием. Разница = changes этой сессии. Сложнее, но точнее.

**Минимальный фикс:** Исключить binary файлы из diffs (`*.exe`, файлы без расширения которые `file` определяет как binary). Это не решит phantom, но уберёт самый шумный артефакт.

## Прецедент #2 — сессия ee202e0b (autodev-v2, 2026-04-09)

Сессия работала с 7 файлами. В artifacts попали 3 phantom:
- `docs/2. specifications/ADV-S05_go_intra_project_orchestration.md` (modified) — не трогали
- `docs/3. tasks/ADV-S05_go_intra_project_orchestration/ADV-T049_s05_structured_markdown_parser.md` (deleted) — не трогали
- `docs/ADV-CHANGELOG.md` (modified) — не трогали

Все три присутствовали в `git status` как uncommitted changes из **предыдущей** сессии.
Зафиксировано через `/verify-archive` и исправлено вручную в export .md + SQLite.

## Прецедент #3 — сессия 51cb90a9 (autodev-v2, 2026-04-09)

Сессия `/codereview T028`: реально тронула 6 файлов (task file modified + 5 read). В artifacts попали 5 phantom:
- `docs/2. specifications/ADV-S05_go_intra_project_orchestration.md` (modified) — не трогали
- `docs/3. tasks/ADV-S05.../ADV-T049...md` (deleted) — не трогали
- `docs/ADV-CHANGELOG.md` (modified) — не трогали
- `docs/ADV-HANDOFF.md` (modified) — не трогали
- `internal/runner/handoff_sync.go` (modified) — не трогали

Все пять присутствовали в `git status` как uncommitted changes из предыдущих сессий (зафиксировано в gitStatus в system-reminder). Исправлено вручную в export .md + SQLite.

Паттерн устойчив: баг воспроизводится в каждой сессии, где есть uncommitted changes в worktree.

## Прецедент #4 — сессия 837e25fc (sproektirui, 2026-04-09)

Сессия `/codereview-free T148` + `/fix T148`: реально тронула **2 файла** (T148 task file + SeriesModal.jsx). В artifacts попали 11 phantom:
- `.claude/commands/codereview-local.md` (modified) — не трогали
- `.claude/settings.local.json` (modified) — не трогали
- `Docs/3. tasks/S15_sprint4/T147...md` (deleted) — не трогали
- `Docs/3. tasks/S15_sprint4/T149...md` (modified) — не трогали
- `Docs/3. tasks/S15_sprint4/T150...md` (deleted) — не трогали
- `Docs/CHANGELOG.md` (modified) — не трогали
- `teplofort1-app/e2e/report/index.html` (modified) — не трогали
- `teplofort1-app/e2e/screenshots/local-dev/02-known-result.png` (modified) — не трогали
- `teplofort1-app/e2e/screenshots/prod-desktop/05-block3-full-state.png` (modified) — не трогали
- `teplofort1-app/e2e/screenshots/prod-desktop/05-connection-type-selector.png` (modified) — не трогали
- `teplofort1-app/frontend/src/components/heating/DeviceCalculator.jsx` (modified) — не трогали

Все 11 присутствовали в git status как uncommitted changes от предыдущей сессии (T147+T149+T150 из коммита `7afeb15`). Были соответствующие diffs (1835 строк лишнего контента, включая binary-like PNG patches).

Исправлено вручную: DELETE 11 строк из session_artifacts + удаление phantom diff-блоков из export .md.

## Прецедент #5 — session fb6419f7 (sproektirui, 2026-04-09)

Сессия `/codereview-local T149`: **read-only** (0 Edit/Write), реально прочитано 4 файла. В artifacts попали 14 phantom из git status: codereview-local.md, settings.local.json, S15_sprint4.md, T147 (deleted), T148 (modified), T150 (deleted), CHANGELOG.md, HANDOFF.md, e2e/report/index.html, 3× screenshots (PNG), t149-tooltip-check.spec.js, SeriesModal.jsx. Плюс 2240 строк phantom diffs при 0 реальных (read-only сессия = 0 diffs).

**Ключевое:** read-only сессия с 0 реальных diffs делает баг максимально очевидным — 100% Diffs секции phantom. Исправлено вручную.

## Прецедент #6 — session 1dbec8ba (sproektirui, 2026-04-09)

Сессия `/visualcheck T148`: реально тронула **1 файл** (T148 task file, Edit) + 7 скриншотов (created via MCP Playwright) + 1 file read (SeriesModal.jsx). В artifacts попали 15 phantom из git status: codereview-local.md, settings.local.json, S15_sprint4.md, T147 (deleted), T149, T150 (deleted), CHANGELOG.md, HANDOFF.md, e2e/report/index.html, 3× screenshots (.png), t149-tooltip-check.spec.js, DeviceCalculator.jsx, SingletonLock (deleted). Phantom diffs = ~2160 строк (из ~2760 total).

Дополнительно: MCP-созданные скриншоты (через `mcp__playwright__browser_take_screenshot`) **не попали** в artifacts — парсер не отслеживает MCP tool calls как источник артефактов. Исправлено вручную.

## Прецедент #7 — session d3dae777 (sproektirui, 2026-04-09)

Сессия `/visualcheck + /smoketest T149`: реально тронула **1 файл** (T149 task file, Edit) + 6 read (HANDOFF.md, DeviceCalculator.jsx, badge.jsx, calc_service.py, t149-tooltip-check.spec.js, t149-vc-12-hover-badge.png). В artifacts попали 13 phantom из git status: codereview-local.md, settings.local.json, S15_sprint4.md, T147 (deleted), T148, T150 (deleted), CHANGELOG.md, e2e/report/index.html, 3× screenshots (.png), SeriesModal.jsx, + 1 subagent temp file. Phantom diffs = ~1967 строк.

Паттерн идентичен прецедентам #4-#6: те же самые файлы из git status (uncommitted changes от коммита `7afeb15`). Исправлено вручную.

## Прецедент #8 — session 29ff92a9 (autodev-v2, 2026-04-09)

Сессия `/intro` + анализ ADV-T045: **read-only** (0 Edit/Write), реально прочитано 3 файла (HANDOFF, CHANGELOG, T045 task doc). В artifacts попали 15 phantom из git status: binary `adv`, `cmd/adv/main.go`, 2× specs (S04, S05), 2× deleted task files (T028, T049), 6× internal Go files (executor, pipeline, runner, state), `docs/ADV-CHANGELOG.md`, `docs/ADV-HANDOFF.md`. Phantom diffs = ~2200 строк (включая 450-строчный binary patch для `adv`), export file раздулся до 65K tokens (2531 строк) вместо ~300 строк.

Дополнительная проблема: событие `spec_read` ложное — читали task doc (`docs/3. tasks/...`), не spec (`docs/2. specifications/...`). Парсер перепутал task с spec.

**100% Diffs секции phantom** (read-only сессия = 0 реальных diffs). Исправлено: удалены 15 phantom artifacts из SQLite, заменена Diffs секция на пустую, event `spec_read` → `task_read`, `manually_reviewed = 1`.

## Acceptance Criteria

- [ ] Artifacts содержат только файлы из tool calls текущей сессии (Read → read, Edit/Write → modified)
- [ ] Diffs содержат только файлы с Edit/Write tool calls текущей сессии
- [ ] Binary файлы не генерируют diff patches
- [ ] Файлы из `git status` без tool call evidence НЕ попадают в artifacts
