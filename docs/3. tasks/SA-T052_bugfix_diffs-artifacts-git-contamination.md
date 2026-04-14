**Дата:** 2026-04-08
**Статус:** open
**Severity:** HIGH

# SA-T052 — Diffs и Artifacts загрязнены pre-existing uncommitted git changes

## Проблема

Парсер использует `git diff HEAD` для генерации секции Diffs. Это захватывает ВСЕ uncommitted changes в репозитории, включая изменения из предыдущих сессий. Аналогично, Artifacts включают файлы из `git status` которые были изменены до начала текущей сессии.

Результат: экспорт содержит diffs/artifacts чужих сессий, создавая ложное впечатление что текущая сессия трогала эти файлы.

## Воспроизведение (2026-04-08, session d62bc616)

1. Репозиторий имеет 8 uncommitted файлов из предыдущей сессии (S04 spec, T024, T025, T028, T045, CHANGELOG, HANDOFF, architecture)
2. Текущая сессия модифицирует только 1 файл (T048 task md)
3. `archive-current` записывает 9 diffs (1 реальный + 8 фантомных) и 18 artifacts (10 реальных + 8 фантомных)
4. Фантомные diffs содержат полное удаление T024 (140 строк) и T025 (113 строк) — файлы перемещены в Done/ в предыдущей сессии

## Корневая причина

`git diff HEAD` не имеет понятия "session boundary". Любые uncommitted changes попадают в diff, независимо от того, кто и когда их сделал.

## Рекомендация по фиксу

**Опция A (session-aware diff):**
1. При `archive-current` запоминать список файлов, которые реально трогались tool calls текущей сессии (Edit, Write, Bash mv/rm)
2. Генерировать diffs ТОЛЬКО для этих файлов: `git diff HEAD -- <file1> <file2> ...`
3. Для файлов не в git (new/deleted) — генерировать synthetic diff только если файл в списке tool calls

**Опция B (tool-call-based diff):**
1. Извлекать содержимое до/после из самих tool calls (Edit old_string/new_string, Write content)
2. Не зависеть от git вообще — diff строится из JSONL
3. Плюс: работает даже если репозиторий dirty. Минус: не видит side-effects (файлы изменённые Bash командами)

**Опция C (snapshot-based):**
1. При старте сессии сохранить `git stash list` или snapshot of `git status`
2. В конце — diff только новых изменений
3. Минус: требует hook на начало сессии

Рекомендую Опцию A как минимально инвазивную: парсер уже знает какие файлы трогала сессия (из tool calls), нужно только использовать этот список как фильтр для `git diff`.

### Новое воспроизведение (2026-04-08, session e78a1b60)

Сессия: code review ADV-T032. Модифицирован 1 файл (T032 task md). Парсер записал:
- **18 phantom artifacts** включая: `$FIXTURE_DIR"/*`, `smoketest_harness_t032_test.go`, `test_regex_t032_test.go`, `/tmp/smoketest-T032-*` — файлы из предыдущей smoke test сессии. `adv` (бинарь Go), 8 docs/* файлов из uncommitted branch changes.
- **11 phantom diffs** — `adv` binary diff (5MB!), S04 spec, T024/T025/T048 task files (deleted/moved in prior session), CHANGELOG, HANDOFF, architecture — всё от branch, не от сессии.

**Cascading effect:** phantom diff содержит `## Smoke Test` секцию → skill detector извлекает ложный тег `skill: smoketest`. Фантомные diffs не только засоряют export, но и отравляют другие парсеры (skills, events).

### Новое воспроизведение (2026-04-08, session 1b9bfce0)

Сессия: независимый код-ревью ADV-T032 (autodev-v2). Модифицирован 1 файл (T032 task md). Парсер записал:
- **9 phantom artifacts** (modified/deleted): `adv` (Go binary!), S04 spec, T024/T025/T048 task files (deleted), T028, T045, CHANGELOG, architecture — все из uncommitted branch changes
- **9 phantom diffs** из 10 — включая **5MB binary diff** для `adv` (Go compiled binary). Только T032 task file diff был реальным
- Phantom diffs составили ~1127 строк из ~1440 (78%) секции Diffs

**Новый аспект: binary artifact.** `adv` — скомпилированный Go бинарь, попавший в git diff как binary patch (delta 5.4MB). Парсер не фильтрует бинарные файлы, создавая огромный бесполезный export.

**Дополнительный каскадный эффект:** phantom diff T048 содержит секции `## Code Review` и `## Smoke Test` → skill detector извлёк ложный тег `skill: fix` (из текста `### Fix Verification`).

### Рекомендация: дополнительно к фиксу diff-фильтрации

После фикса SA-T052, skill/event/task детекторы перестанут получать phantom контент из чужих сессий. Но для defence-in-depth — skill detector не должен сканировать diff content (секцию `## Diffs`), только assistant messages и tool calls.

### Новое воспроизведение (2026-04-08, session 336dd55e)

Сессия: код-ревью + фиксы T032 + правка промптов codereview.md и smoketest.md (autodev-v2). Модифицировано 5 файлов (T032 task md, runner.go, handoff_sync_test.go, codereview.md, smoketest.md). Парсер записал:
- **10 phantom artifacts** (modified/deleted): `adv` (Go binary), S04 spec, T024/T025/T048 (deleted), T028, T045, CHANGELOG, architecture — все из uncommitted branch changes
- **10 phantom diffs** из 13 — включая 5MB binary diff для `adv`. Только 3 diffs реальные (T032 task file, runner.go, handoff_sync_test.go)
- **2 missing diffs** — codereview.md и smoketest.md не захвачены (файлы вне git repo `/Users/is/.claude/commands/`)
- Каскадный эффект: phantom diff content отравил skill detector → ложные теги `codereview` и `smoketest`

**Новый аспект: missing non-git artifacts.** Файлы `/Users/is/.claude/commands/*.md` модифицировались через Edit tool, но не попали в diffs потому что `git diff HEAD` работает только внутри git repo проекта. Для файлов вне repo нужен synthetic diff из tool call history (SA-T058 adjacent).

### Новое воспроизведение (2026-04-08, session b37b5341)

Сессия: ревью + фиксы ADV-T049 task spec (autodev-v2). Модифицирован 1 файл (T049 task md, 4 Edit calls). Парсер записал:
- **15 phantom artifacts** (modified/deleted): `adv` (Go binary), `cmd/adv/main.go`, S04/S05 specs, T024/T025/T032/T048 (deleted), T028, T045, T029, T031, CHANGELOG, architecture, `config.go`, `runner.go` — все из uncommitted branch changes
- **18 phantom diffs** из 19 — включая 5MB binary diff для `adv`. Только 1 diff реальный (T049 synthetic)
- Phantom diffs = ~1840 строк из ~1930 total (95%)
- Каскадного отравления skill/event detector не зафиксировано (tags корректны)

**Ручной фикс:** удалены 15 phantom artifacts из SQLite (`diff_source='git_head'`), вырезаны 18 phantom diffs из export .md. Осталось 5 реальных артефактов и 1 synthetic diff.

### Новое воспроизведение (2026-04-09, session 837e25fc, sproektirui)

Сессия: независимый код-ревью T147 (5-й проход) + фикс (`whitespace-nowrap → truncate`) + accept (move to Done, HANDOFF/CHANGELOG/spec update). Реально изменено 5 файлов (DeviceCalculator.jsx, CHANGELOG.md, HANDOFF.md, S15_sprint4.md, T147 task file moved to Done). Парсер записал:

- **10 phantom artifacts** (modified/deleted): T148_series_modal_sticky_scrolls.md, SeriesModal.jsx, codereview-local.md, settings.local.json, T149_power_tag_tooltips.md, T150_connection_images.md (deleted), e2e/report/index.html, 2×screenshots/prod-desktop, t149-tooltip-check.spec.js — все из uncommitted branch changes до старта сессии (видны в `git status` в начале разговора)
- **9 phantom diffs** из 14 — 8 файлов из предыдущих сессий + binary screenshots (base64). Реальные diffs: T147 (deleted/moved), CHANGELOG.md, DeviceCalculator.jsx
- **Tasks ложные**: `T042, T148` вместо `T147`. T148 попал из phantom diff T148_series_modal (каскадный эффект парсера задач). T042 — неизвестный источник (возможно из skill template или HANDOFF context).
- **Missing artifacts**: HANDOFF.md и S15_sprint4.md классифицированы как (read) хотя были изменены; T147_done.md (created в Done/) не попал т.к. untracked new file невидим в `git diff HEAD`

**Новый аспект: Tasks cascade from phantom diffs.** Парсер задач извлёк T148 из содержимого phantom diff T148_series_modal_sticky_scrolls.md. Это подтверждает выводы SA-T052 / SA-T052 рекомендацию: skill/event/task детекторы не должны сканировать `## Diffs` секцию.

**Новый аспект: untracked created files.** `git diff HEAD` не видит новые untracked файлы (только tracked modified/deleted). T147_done.md создан через `cp + rm` (Bash), что создаёт untracked файл в Done/ — он не попадает ни в diff, ни в artifacts. Для захвата нужен анализ Bash tool calls с паттернами `cp ... Done/`, `mv ... Done/`.

**Ручной фикс (2026-04-09):** удалены 10 phantom artifacts из SQLite, исправлены action для HANDOFF.md и S15_sprint4.md (read→modified), добавлены 8 реальных artifacts (created Done file + 7 read files). Tasks: T042/T148 → T147. Export .md: секция Artifacts пересобрана, phantom diffs помечены комментарием `<!-- ⚠️ PHANTOM SA-T052 -->`.

### Новое воспроизведение (2026-04-09, session fb6419f7, sproektirui)

Сессия: независимый код-ревью T149 (read-only, ни одного Edit/Write). Реально прочитано 4 файла (T149 task, REVIEW.md, DeviceCalculator.jsx, schemas/calc.py). Парсер записал:

- **14 phantom artifacts** (modified/deleted): codereview-local.md, settings.local.json, S15_sprint4.md, T147 (deleted), T148 (modified), T150 (deleted), CHANGELOG.md, HANDOFF.md, e2e/report/index.html, 3× screenshots (PNG), t149-tooltip-check.spec.js, SeriesModal.jsx — все из uncommitted changes предыдущей сессии
- **2 phantom bash artifacts** (SA-T056/SA-T070): `routers/calc.py` из grep output, `ResultTabs.js` (должно быть `.jsx`)
- **2240 строк phantom diffs** из 0 реальных — **read-only сессия не должна иметь ни одного diff**. Все diffs пришли из `git status` uncommitted changes
- **Summary overwrite**: при повторном запуске `archive-current` (JSONL обновился с verify-archive) парсер перезаписал корректный summary T149 на T148 (из содержимого phantom diff? или из cross-session JSONL контента)

**Новый аспект: read-only session = 0 diffs.** Ранее phantom diffs маскировались среди реальных. В read-only сессии phantom diffs — 100% секции Diffs, что делает баг очевидным.

**Новый аспект: summary cascade.** Rerun archive-current не просто добавляет phantom artifacts — он перезаписывает summary из JSONL-контента предыдущих сессий. Summary T148 появился из cross-session contamination в JSONL (JSONL файл = Claude Code session, содержащий несколько user conversations).

**Ручной фикс (2026-04-09):** удалены 16 phantom artifacts из SQLite (14 git_head + 2 bash), удалены 2240 строк phantom diffs из export .md (заменены комментарием), summary восстановлен вручную, manually_reviewed=1 установлен.

### Новое воспроизведение (2026-04-09, session c984d918, sproektirui)

Сессия: независимый код-ревью T149 (3rd pass) + фиксы (variant="outline", truncate, dead code) + deploy на stage + verify. Реально изменено 4 файла: DeviceCalculator.jsx, SeriesReview.jsx, codereview-local.md, T149 task file. Commit `054cb06`. Парсер записал:

- **9 phantom artifacts** (modified/deleted): T147 (deleted), T148 (modified), T150 (deleted), CHANGELOG.md, e2e/report/index.html, 3× screenshots (PNG binary), remote server path `/home/ivan/.../DeviceCalculator.js` — все из commit `7afeb15` (предыдущей сессии) или `git status` uncommitted
- **8 phantom diffs** из 13 — T147 (575 строк!), T148 (38 строк), T150 (75 строк), CHANGELOG (16 строк), e2e/report (base64 binary), 3× screenshots (base64 binary, ~1400 строк) = **~1734 строк phantom diffs** из ~2082 total (83%)
- **Tasks ложный**: T042 попал из skill template `/archive-session` (каскад SA-T066)
- **Skills ложные**: `codereview`, `codereview-local`, `smoketest` попали из модификации файлов скиллов и контента ревью (каскад SA-T068, SA-T064)

**Новый аспект: committed branch changes.** Ранее phantom diffs были от uncommitted changes в working tree. В этой сессии все phantom diffs — из ПРЕДЫДУЩИХ КОММИТОВ на ветке `dev` (commit 7afeb15 и ранее). `git diff main..dev` захватывает все коммиты ветки, а не только текущей сессии. Fix для uncommitted changes (фильтр по tool calls) НЕ решит эту проблему — нужен `base_commit` snapshot.

**Рекомендация:** при `archive-current` сохранять `base_commit` (HEAD на момент начала сессии, доступен из JSONL metadata или передаётся из `/archive-session`). Diffs генерировать как `git diff <base_commit>..HEAD` вместо `git diff main..HEAD`. Для uncommitted — `git diff HEAD -- <tool-call-files>`.

**Ручной фикс (2026-04-09):** удалены 9 phantom artifacts из SQLite, вырезаны 1734 строки phantom diffs из export .md. Tasks: T042 → удалён. Skills: codereview, codereview-local, smoketest → удалены. Осталось 13 реальных артефактов и 5 реальных diffs.

### Новое воспроизведение (2026-04-09, session 1da68ce5, sproektirui)

Сессия: код-ревью T149 (4th pass, `/codereview`). Реально изменён 1 файл (T149 task file, +1 Edit call). Парсер записал:

- **9 phantom artifacts** (modified/deleted): `.claude/settings.local.json`, T147 (deleted), T148 (modified), T150 (deleted), `CHANGELOG.md`, `e2e/report/index.html`, 3× screenshots (PNG) — все из uncommitted `git status` changes
- **1 phantom artifact wrong ext**: `DeviceCalculator.js` (should be `.jsx`) — SA-T070
- **9 phantom diffs** из 10 — settings.json, T147 (deleted, 205 строк), T148 (modified), T150 (deleted, 67 строк), CHANGELOG, e2e/report (binary), 3× screenshots (binary base64, ~1800 строк) = **~1800 строк phantom diffs** из ~2160 total (83%)
- **Tasks cascade**: T042, T099 из skill templates (SA-T066)
- **Skills cascade**: `codereview-local` из Read tool на config file (SA-T068)
- **Domain wrong**: `docs` вместо `frontend` — код-ревью React-компонентов неверно классифицирован

**Ручной фикс (2026-04-09):** удалены 10 phantom artifacts из SQLite, вырезаны ~1800 строк phantom diffs из export .md. Tasks: T042, T099 → удалены. Skills: codereview-local → удалён. Domain: docs → frontend. Events: lint_run добавлен. Осталось 11 реальных артефактов и 1 реальный diff.

### Новое воспроизведение (2026-04-09, session 891fbac2, sproektirui)

Сессия: код-ревью T153 (WindowVisualization.jsx, DeviceCalculator.jsx, ResultTabs.jsx). Реально изменён 1 файл (T153 task file). Парсер записал:

- **3 phantom artifacts** (modified): `.claude/commands/codereview-local.md`, `.claude/settings.local.json`, `T152_s15_hidden_brand_bug.md` — все из uncommitted `git status` changes предыдущих сессий
- **3 phantom diffs** из 4 — codereview-local.md (33 строк, shadcn gotchas от T149 сессии), settings.local.json (4 строки, additionalDirectories), T152 task file (42 строки, код-ревью T152 от другой сессии)
- **Tasks cascade**: T149 попал из CHANGELOG.md Read content (SA-T049)

Также SA-T071 рецидив: первая попытка `archive-current` захватила JSONL `1763be29` (T152 сессия) вместо `891fbac2` (T153) — multiple files с одинаковым mtime 14:56-14:57, `ls -t | head -1` выбрал не тот.

**Ручной фикс (2026-04-09):** удалены 3 phantom artifacts из SQLite, вырезаны 3 phantom diffs из export .md. Tasks: T149 → удалён. `manually_reviewed=1`. Осталось 8 реальных артефактов и 1 реальный diff.

### Новое воспроизведение (2026-04-09, session f8a14e62, sproektirui)

Сессия: `/visualcheck T151` — visual check на stage.priborpodbor.ru через Playwright. Реально изменён 1 файл (T151 task file, +1 Edit добавляющий Visual Check секцию). Парсер записал:

- **5 phantom artifacts** (modified): `.claude/commands/codereview-local.md`, `.claude/settings.local.json`, `T152_s15_hidden_brand_bug.md`, `T153_s15_installation_visualization.md`, `e2e/report/index.html` — все из uncommitted `git status` changes предыдущих сессий
- **5 phantom diffs** из 6 — codereview-local.md (36 строк, shadcn gotchas), settings.local.json (4 строки), T152 task file (97 строк, код-ревью T152), T153 task file (76 строк, код-ревью T153), e2e/report (binary base64 diff) = **~273 строк phantom diffs**
- **Tasks cascade**: T042, T099 из skill templates (SA-T057/SA-T066)
- **Domain wrong**: `docs` вместо `frontend` (SA-T008 рецидив)

**Ручной фикс (2026-04-09):** удалены 5 phantom artifacts из SQLite, вырезаны 273 строки phantom diffs из export .md (Python скрипт). Tasks: T042, T099 → удалены. Domain: docs → frontend. Осталось 15 реальных артефактов и 1 реальный diff.
