# Session Archive — Handoff Document

**Последнее обновление:** 2026-04-03
**Статус:** Базовая функциональность работает. БД накапливает сессии с 2026-02-25. SA-T009..T015 выполнены — первая волна багов. SA-T016/T019/T020/T022 выполнены — вторая волна. SA-T023..T025/T027/T028 выполнены — третья волна. SA-T021/T026/T030 выполнены — четвёртая волна. SA-T032/T034/T036 выполнены — пятая волна (session boundary, manually_reviewed guard, summary meta-filter, git ls-files для Write action). SA-T017/T033 выполнены — шестая волна (archive boundary для artifact extraction, shell-read trace). SA-T018/T031/T035 выполнены — седьмая волна (git-status enrichment, artifact lifecycle, diff quality). SA-T029 выполнен — восьмая волна (EvidenceAccumulator архитектура, evidence-based domain tags, BUG-TAGS-DOMAIN-DATABASE-FALSE исправлен).

---

## Краткое резюме проекта

**Session Archive** — локальный инструмент для сохранения и анализа диалогов с AI-ассистентами (Claude Code, OpenAI Codex).

**Зачем:** каждая сессия с AI — это знания, решения и контекст. Без архива они теряются. Архив позволяет:
- видеть историю работы по проектам
- отслеживать какие задачи сколько сессий занимают
- анализировать активность (deploy, tests, commits)
- передавать контекст между сессиями через HANDOFF

**Type:** Solo project, personal tool

---

## Структура документации

```
12_SessionArchive/
├── docs/
│   ├── SA-architecture.md          ← технические детали, DB схема, data flow
│   ├── SA-HANDOFF.md               ← этот файл
│   ├── SA-CHANGELOG.md             ← история изменений
│   ├── 1. business requirements/   ← пусто (solo проект, BR неформальные)
│   ├── 2. specifications/          ← спеки фич
│   ├── 3. tasks/Done/              ← выполненные задачи
│   ├── 4. guides/                  ← конвенции документации
│   ├── 5. unsorted/                ← черновики и ресёрч
│   └── 6. backlog/                 ← идеи будущих фич
└── README.md                       ← быстрый старт
```

---

## Что уже сделано

### Ядро (работает)
- [x] SQLite БД с WAL режимом и foreign keys
- [x] Парсинг Claude Code JSONL (полный: messages, tool_calls, artifacts, events)
- [x] Парсинг Codex JSONL (частичный: метаданные без транскрипта)
- [x] Автодетект формата JSONL (`detect_jsonl_format`)
- [x] Экспорт markdown транскриптов в `data/exports/`
- [x] Команда `archive-current` — автоматический поиск JSONL текущей сессии
- [x] Команда `stats` — быстрая статистика в терминале
- [x] Команда `query` — произвольный SQL к БД
- [x] Эволюция схемы через `_ensure_column()` (без поломок при обновлении)
- [x] `agent_family` автоопределение: claude / codex / unknown

### Аналитика (работает)
- [x] `analyze.py` с отчётами: summary, projects, tasks, events, domains, timeline, artifacts, models, deep
- [x] Datasette совместимость (опциональный web UI)

### Интеграция
- [x] `/archive-session` skill для Claude Code
- [x] Глобальный навык в `~/.claude/commands/archive-session.md`
- [x] Настроен как стандартная завершающая команда сессий

### Данные
- [x] ~80+ сессий в БД с 2026-02-25 по сегодня
- [x] Покрытые проекты: autodev-v2, cleaning-bot, sales, SessionArchive, VPN, sproektirui

---

## Текущее состояние

**Рабочее:** `/archive-session` вызывается в конце сессий → пишет в БД → экспортирует markdown.

**Известные ограничения:**
- Кодекс-сессии пишут только метаданные, транскрипт пустой
- `session_archive.backup.2026-03-27.py` — резервная копия старой версии, не удалять до полной проверки
- Нет веб-интерфейса из коробки (только Datasette опционально)
- Нет уведомлений о новых сессиях

**Файл с багами:** [BUGS.md](../BUGS.md)

---

## Активные задачи

| Задача | Описание | Статус |
|--------|----------|--------|
| ~~[SA-T001](3.%20tasks/Done/SA-T001_bugfix_parser-model-tags_done.md)~~ | ~~Исправить парсинг модели (BUG-34) и мусорных тегов (BUG-TAGS-XML)~~ | ✅ done 2026-04-03 |
| ~~[SA-T002](3.%20tasks/Done/SA-T002_bugfix_diff-formatting_done.md)~~ | ~~Исправить форматирование diff-блоков (двойные слеши, пустые строки, untracked scope)~~ | ✅ done 2026-04-03 |
| ~~[SA-T003](3.%20tasks/Done/SA-T003_bugfix_tasks-false-positive_done.md)~~ | ~~Исправить BUG-TASKS-FALSE-POSITIVE: фантомные задачи из контекста~~ | ✅ done 2026-04-03 |
| ~~[SA-T004](3.%20tasks/Done/SA-T004_bugfix_events-detection_done.md)~~ | ~~Исправить детекцию событий: phantom events из regex + добавить session_archived~~ | ✅ done 2026-04-03 |
| ~~[SA-T005](3.%20tasks/Done/SA-T005_bugfix_slug-query-commit_done.md)~~ | ~~Исправить PROJECT_SLUG (leading dash) и conn.commit() в cmd_query~~ | ✅ done 2026-04-03 |
| ~~[SA-T006](3.%20tasks/Done/SA-T006_bugfix_tasks-summary-context-drift_done.md)~~ | ~~Исправить Tasks и Summary: дрейф из контекста (BUG-27/39/17, 49+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T007](3.%20tasks/Done/SA-T007_bugfix_artifacts-bash-mv-rm_done.md)~~ | ~~Исправить Artifacts: mv/rm через Bash не детектируются (BUG-NEW/ARTIFACTS-WRONG-ACTION, 15+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T008](3.%20tasks/Done/SA-T008_bugfix_domain-context-drift_done.md)~~ | ~~Исправить domain-теги: дрейф из текста диалога (BUG-TAGS-CONTEXT-DRIFT, 13+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T009](3.%20tasks/Done/SA-T009_bugfix_diff-full-file-synthetic_done.md)~~ | ~~Исправить diff: весь файл как новый для untracked/large файлов (BUG-DIFF-SCOPE/WRONG-HUNK, 19+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T010](3.%20tasks/Done/SA-T010_bugfix_assistant-tag-model-id_done.md)~~ | ~~Исправить assistant/model теги: захардкожен "claude" (BUG-ASSISTANT-TAG-VALUE, 5+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T011](3.%20tasks/Done/SA-T011_bugfix_archive-integrity_done.md)~~ | ~~Целостность повторной архивации: overwrite guard + mtime precision + session_id check (9+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T012](3.%20tasks/Done/SA-T012_bugfix_phantom-skill-tags_done.md)~~ | ~~Фантомные skill-теги из XML-маркеров и prose (BUG-SKILL-XML/PHANTOM, 8+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T013](3.%20tasks/Done/SA-T013_bugfix_message-duplicates_done.md)~~ | ~~Дубли сообщений в session_messages и Transcript (BUG-14/BUG-21, 7+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T014](3.%20tasks/Done/SA-T014_bugfix_tasks-from-tool-results_done.md)~~ | ~~Task IDs из содержимого tool results (BUG-TASKS-FROM-TOOL-RESULTS, 1+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T015](3.%20tasks/Done/SA-T015_bugfix_artifact-write-action_done.md)~~ | ~~artifact action "created" vs "modified" для Write на tracked файлах (BUG-ARTIFACTS-WRITE-ACTION)~~ | ✅ done 2026-04-03 |
| ~~[SA-T016](3.%20tasks/Done/SA-T016_bugfix_open-issues-content_done.md)~~ | ~~Open Issues заполняется stdout Python-скрипта и reasoning-текстом (BUG-OPEN-ISSUES-CONTENT/REASONING-TEXT, 10+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T017](3.%20tasks/Done/SA-T017_bugfix_artifacts-phantom-context_done.md)~~ | ~~Фантомные артефакты из соседних сессий (BUG-ARTIFACTS-PHANTOM-CONTEXT, 4+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T018](3.%20tasks/Done/SA-T018_bugfix_artifacts-missing-and-diffs_done.md)~~ | ~~Пропущенные артефакты и дифы изменённых файлов (BUG-ARTIFACTS-MISSING + BUG-DIFF-MISSING-TRACKED-FILES, 6+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T019](3.%20tasks/Done/SA-T019_bugfix_pseudo-artifacts-events_done.md)~~ | ~~Pseudo-artifacts event:* в session_artifacts (BUG-22/24/41, 18+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T020](3.%20tasks/Done/SA-T020_bugfix_skill-tags-detection_done.md)~~ | ~~Skill-теги не детектируются из Skill tool calls; timing (BUG-SKILL-MISSING/TIMING, 15+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T021](3.%20tasks/Done/SA-T021_bugfix_synthetic-diff-format_done.md)~~ | ~~Synthetic diff: пустые строки + ложный full-file add для untracked (BUG-40/DIFF-FMT/BUG-12, 21+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T022](3.%20tasks/Done/SA-T022_bugfix_artifact-operation-classification_done.md)~~ | ~~Классификация операций артефактов: created/modified/moved, cwd-фильтр, is_error (BUG-ARTIFACT-WRONG-OP/MISSING-MOVE/OUTSIDE-CWD/FAILED-EDIT, 6+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T023](3.%20tasks/Done/SA-T023_bugfix_jsonl-integrity_done.md)~~ | ~~JSONL integrity: float mtime + unique constraints (BUG-WRONG-JSONL/JSONL-MTIME/SQLITE-NO-UNIQUE-CONSTRAINT, 3+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T024](3.%20tasks/Done/SA-T024_bugfix_skill-detection-command-message_done.md)~~ | ~~Skill detection из command-message тегов (BUG-SKILL-TAGS-SLASH-COMMAND/TAGS-SKILL-MISSING, 2+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T025](3.%20tasks/Done/SA-T025_bugfix_slug-underscore-to-dash_done.md)~~ | ~~PROJECT_SLUG underscore → dash (BUG-SLUG-UNDERSCORE-TO-DASH)~~ | ✅ done 2026-04-03 |
| ~~[SA-T026](3.%20tasks/Done/SA-T026_bugfix_summary-accuracy_done.md)~~ | ~~Summary accuracy: archive-boundary + task-file priority (5+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T027](3.%20tasks/Done/SA-T027_bugfix_bash-parsing-fixes_done.md)~~ | ~~Bash parsing: shell vars, task IDs из mv, дубли диффов, shlex (3+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T028](3.%20tasks/Done/SA-T028_bugfix_artifact-noise-reduction_done.md)~~ | ~~Artifact noise: ide_opened_file, Glob, skill-примеры, config-read (3+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T029](3.%20tasks/Done/SA-T029_arch_evidence-based-extraction_done.md)~~ | ~~**Архитектура:** Evidence-based extraction layer — заменить text heuristics (recurring)~~ | ✅ done 2026-04-03 |
| ~~[SA-T030](3.%20tasks/Done/SA-T030_bugfix_regression-integrity_done.md)~~ | ~~Регрессии: overwrite guard, msg-dedup, open_issues fmt (2+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T031](3.%20tasks/Done/SA-T031_bugfix_artifact-session-lifecycle_done.md)~~ | ~~Жизненный цикл артефакта: created+deleted, multi-commit diff (1+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T032](3.%20tasks/Done/SA-T032_bugfix_summary-from-context_done.md)~~ | ~~Summary генерируется из контекста/goals вместо фактического outcome (BUG-SUMMARY-FROM-CONTEXT, 3+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T033](3.%20tasks/Done/SA-T033_bugfix_shell-read-trace_done.md)~~ | ~~Artifacts пусты/неполны: bash shell-read trace не захватывается (BUG-ARTIFACTS-PARTIAL/EMPTY, 3+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T034](3.%20tasks/Done/SA-T034_bugfix_artifacts-wrong-session_done.md)~~ | ~~Artifacts: файлы из предыдущих сессий попадают без timestamp-фильтрации (BUG-ARTIFACTS-WRONG-SESSION, 2+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T035](3.%20tasks/Done/SA-T035_bugfix_diff-synthetic-modified_done.md)~~ | ~~Diff: whole-file synthetic для modified untracked + wrong-file из worktree (BUG-DIFF-SYNTHETIC/WRONG-FILE, 2+ сессий)~~ | ✅ done 2026-04-03 |
| ~~[SA-T036](3.%20tasks/Done/SA-T036_bugfix_rerun-overwrite-regressions_done.md)~~ | ~~archive-current re-run уничтожает ручные правки + регрессии action/event (BUG-RERUN-OVERWRITE + 2 регрессии)~~ | ✅ done 2026-04-03 |
| ~~[SA-T037](3.%20tasks/Done/SA-T037_s01_context-window-whitelist_done.md)~~ | ~~Реализовать SA-S01: context-window whitelist для session boundary (`--tool-ids` в archive-current + обновление скилла)~~ | ✅ done 2026-04-03 |

---

## Следующие шаги (backlog)

### Новые баги (2026-04-06)

| ID | Баг | Приоритет |
|----|-----|-----------|
| BUG-JSONL-SELECTION | При нескольких JSONL с одинаковым mtime `ls -t` выбирает случайный файл → захватывается неверная сессия. Воспроизведено: `6485a856` выбран вместо `bccab769` — Summary, Artifacts, Diffs полностью из прошлой сессии (ADV-S08 вместо ADV-S05). **Фикс:** использовать `ls -lt` с полными временными метками или сравнивать `stat -f %m` | P0 |
| BUG-ARTIFACTS-MODIFIED-UNTRACKED | Файлы изменённые через Edit/Write tool, но untracked в git (новые файлы), не попадают в Artifacts. ADV-S05 — главный файл правок сессии — отсутствовал. **Фикс:** добавить в artifact extractor detekцию Edit/Write tool calls с путями к untracked файлам | P0 |
| BUG-ARTIFACTS-GIT-STAGED | В Artifacts попадают файлы из git staging area (D-staged, M-staged из предыдущих коммитов), которые не трогались в текущей сессии. ADV-CHANGELOG.md, ADV-architecture.md, test_concurrent.sh появились как (modified)/(deleted) хотя сессия их не касалась. **Фикс:** git-status фильтр должен пересекаться с timestamp-фильтром tool calls | P1 |
| BUG-VERIFY-ARCHIVE-OVERWRITES | `/verify-archive` перезаписывает export и SQLite игнорируя `manually_reviewed=1`. После ручного исправления Summary через archive-session, verify-archive восстановил неправильный Summary из предыдущей сессии. Регрессия SA-T036. **Фикс:** verify-archive должен проверять `manually_reviewed` флаг перед overwrite | P1 |
| BUG-SKILL-FALSE-POSITIVE-CODEREVIEW | `skill: codereview` тег появляется без реального Skill tool call. Воспроизведено в bccab769: скилл не запускался, тег присутствует. Вероятно, text-match на слово "ревью" в диалоге. **Фикс:** skill tags должны детектироваться только из Skill tool call events, не из prose | P2 |
| BUG-ARTIFACT-ACTION-READ-ON-MODIFIED | Существующий файл (tracked или untracked) попадает в Artifacts с action=read, если в той же сессии был и Read и Edit tool call. Воспроизведено в 52f3734e: PROFILE.md был прочитан и изменён, но action=read. Проект без git — git status не возвращает M-статус. Парсер берёт action от первого инструмента (Read), не обновляет при наличии Edit. **Фикс:** при наличии Edit tool call на файл — action должен быть modified, независимо от наличия Read | P1 |
| BUG-TASKS-PHANTOM-FROM-SKILL-EXAMPLES | Task IDs из шаблонов/примеров в skill-файлах (codereview.md example: `T042`, `T{ID}`) попадают в session_tasks. Воспроизведено в 5fbee187: T042 — phantom из template. Также воспроизведено в 58fb4abd: T001, T042 — фантомы из `/smoketest` skill template (пример "task T001 started", формат "T042, t042, 042"). **Также воспроизведено в c065e247:** T001, T042 — фантомы из `/smoketest` skill template; T024 — фантом из branch diffs (git status D). Работали только с ADV-T025. **Фикс:** не извлекать task IDs из tool results содержащих skill definitions (content_type=skill_expansion) или из файлов `~/.claude/commands/*.md` | P1 |
| BUG-SKILL-TAG-FROM-SYSTEM-REMINDER | `skill:smoketest` тег появляется без Skill tool call. Воспроизведено в 5fbee187: слово "smoketest" присутствовало в system-reminder (skill listing) и в тексте task file review findings, но /smoketest никогда не вызывался. Аналогичен BUG-SKILL-FALSE-POSITIVE-CODEREVIEW. **Фикс:** skill tags ТОЛЬКО из `Skill` tool_use calls с `skill` parameter, не из prose/system-reminders | P1 |
| BUG-ARTIFACTS-MISSING-OUTSIDE-REPO | Файлы вне git repo (например `~/.claude/commands/codereview.md`), изменённые через Edit tool, не попадают в Artifacts. Воспроизведено в 5fbee187: 2 файла edited но не в artifacts/diffs. **Фикс:** artifact extractor должен учитывать Edit/Write tool calls к файлам вне `cwd`, добавляя их с action=modified | P2 |
| BUG-SKILL-TAG-ARCHIVE-SESSION-MISSING | `skill: archive-session` и `skill: verify-archive` не попадают в теги, несмотря на реальные Skill tool calls. Воспроизведено в 52f3734e и a08e01b9: оба скилла вызваны, оба отсутствуют в tags. **Фикс:** проверить детекцию Skill tool calls — возможно имена со спецсимволами (дефис) не матчатся | P1 |
| BUG-EVENTS-SPEC-MODIFIED-MISSING | Нет события `spec_modified` (или `doc_modified`) при Edit tool calls на spec-файлы. В сессии a08e01b9: 7 Edit calls на ADV-S08, события не отражены. Только `handoff_read` / `spec_read` / `session_archived`. **Фикс:** добавить детекцию Edit/Write calls на `docs/2. specifications/` → событие `spec_modified` | P2 |
| BUG-SESSION-MULTI-LAYER | Один JSONL-файл содержит несколько сессий-разговоров последовательно. Без `--tool-ids` скрипт не умеет определить границу текущей сессии и захватывает старую. Воспроизведено в 9864acab: export.md и транскрипт — от сессии ADV-S06 review, тогда как текущая сессия была ADV-S05 review. Summary, Artifacts, Diffs, Transcript — от чужой сессии. **Также воспроизведено в 4065ce28 (2026-04-12):** `--tool-ids` передан, но transcript всё равно содержит предыдущую сессию (gate-task T055/T056 review); tool_call_count=0 несмотря на 9 tool calls; artifacts и diffs — от git working tree, а не от текущей сессии. `--tool-ids` не помогает ни для transcript, ни для diffs/artifacts scope. **Фикс:** при отсутствии `--tool-ids` использовать временны́е метки tool calls последнего assistant-turn в JSONL как boundary; или всегда требовать `--tool-ids` (fail fast если не переданы) | P0 |
| BUG-GLOB-AS-READ-REGRESSION | Файлы из результатов Glob tool calls попадают в Artifacts как action=read, хотя реально не читались. Воспроизведено в 9864acab: `cmd/adv/main.go` и `internal/config/config.go` появились как (read) — оба файла появились только в результате Glob `internal/**/*.go`, Read calls на них не было. SA-T028 должен был это исправить (Glob noise reduction), но баг воспроизвёлся. Возможна регрессия или неполный фикс для случая когда Glob и Read вызываются на одинаковые файлы в пределах сессии. **Фикс:** Glob results не должны создавать artifact записи; только явные Read tool calls | P1 |
| BUG-JSONL-FIRST-GRAB-WRONG-SESSION | `ls -t` при архивации выбирает JSONL с наибольшим mtime. При нескольких активных сессиях в одном project-dir (разные окна IDE) mtime может указывать на чужую сессию. Воспроизведено в 4f5c78e8: скрипт изначально захватил 084cee39 (сессия ADV-S07 review) вместо 4f5c78e8 (текущая ADV-S06). Также воспроизведено в 58fb4abd: скрипт захватил e701db45 (39 строк, 4 msg — другая сессия code review) вместо 58fb4abd (124 строки, 20 msg — текущая сессия smoke test). Пришлось вручную проверить top-3 по grep и перезапустить. **Фикс:** archive-current должен уметь принять `--session-id` для точного указания нужного JSONL; или skill должен автоматически проверять summary первого захваченного JSONL и переключаться если содержимое не соответствует текущей сессии (детектировать по последнему user-message timestamp) | P1 |
| BUG-DIFF-HANDOFF-BRANCH-SCOPE | Для tracked файлов с `git_head` типом диффа (e.g., HANDOFF.md) в архив попадает полный `git diff HEAD` — все незакоммиченные изменения на ветке. Воспроизведено в 4f5c78e8 и 084cee39: HANDOFF.md изменён на 1-2 строки в текущей сессии, но diff показывает ~200 строк изменений из предыдущих сессий на той же ветке. Происходит когда файл уже был в `git status M` до начала текущей сессии. **Фикс:** для файлов модифицированных через Edit tool в текущей сессии использовать edit_snippet (записывать Edit tool calls) вместо git_head diff; git_head оставить только для файлов которые не трогались через Edit но показывает git status | P1 |
| BUG-SUMMARY-MANUAL-BLOCKS-RERUN | `archive-current --summary "..."` не обновляет `summary` и `summary_manual` в SQLite, если поле `summary_manual` уже непусто — даже при `manually_reviewed=0`. Воспроизведено в 084cee39: первый запуск с `--summary "test"` записал "test" в summary_manual; второй запуск с полным описанием работы → в SQLite по-прежнему "test". Экспорт тоже не обновлён. **Фикс:** `archive-current` должен обновлять `summary` и `summary_manual` при явном `--summary`, если `manually_reviewed ≠ 1`; защита от перезаписи работает только для `manually_reviewed=1` | P1 |
| BUG-MANUALLY-REVIEWED-SILENT-IGNORE | `archive-current --summary "..."` возвращает успех но молча не обновляет summary когда `manually_reviewed=1`. Воспроизведено в 0872f3c0 (ADV-S08 review): передан корректный `--summary`, скрипт отработал без ошибок, вернул session_id, но в SQLite и export остался старый summary от предыдущей сессии (ADV-S04 review). Оператор не знает что его summary проигнорирован до verify-archive. **Фикс:** при `manually_reviewed=1` и явном `--summary` либо обновить summary (сбросив manually_reviewed=0), либо выдать warning "summary not updated: manually_reviewed=1, use --force-summary to override"; silent ignore — худший вариант | P1 |
| BUG-ARTIFACTS-WORKING-TREE-M | Unstaged working-tree `M` файлы (не staged, не тронутые в текущей сессии) попадают в Artifacts как `(modified)`. Воспроизведено в f28b5ca7: 20 файлов ветки `codex/pipeline-hardening-stageb-finalize` из предыдущих сессий (ADV-S04..S08 specs и tasks) появились как артефакты — хотя в текущей сессии они не читались и не изменялись. Также воспроизведено в 016705a0: `ADV-T024_s04_phase_executor.md` попал как (modified) — файл был в git status M от предыдущей сессии, в текущей не трогался ни через Read, ни через Edit. Отличие от BUG-ARTIFACTS-GIT-STAGED: тот баг про staged файлы (индекс), этот — про unstaged `M` статус в рабочем дереве. **Фикс:** artifact extractor должен пересекать `git status --porcelain M`-файлы с timestamp-фильтром Edit/Write tool calls текущей сессии; файлы без Edit/Write в сессии не должны попадать в artifacts | P1 |
| BUG-DIFF-ALL-WORKING-TREE | `git diff HEAD` в секции Diffs захватывает ВСЕ незакоммиченные изменения рабочего дерева на ветке, не только те что изменены в текущей сессии. Воспроизведено в f28b5ca7: 20+ файлов из предыдущих сессий появились в Diffs (~1185 строк ложных diff-ов). Также воспроизведено в 016705a0: `ADV-T024_s04_phase_executor.md` — ~340 строк diff из предыдущей сессии. Также в cc28aef9: diff ADV-T024 показывает ~340 строк (R3-R6) из предыдущих сессий. **Также воспроизведено в 440f2ed2:** ADV-T024 task file — +396 строк diff, из которых ~390 строк (R3-R7 code reviews + smoke tests) — из предыдущих сессий; реальные изменения сессии (~10 строк статус R3 #4 + Fix Verification) не выделимы. **Также воспроизведено в c065e247:** 7 ложных diffs (T024 deleted ~140 строк + T028/T045/T048/CHANGELOG/HANDOFF/architecture modified ~360 строк) — при одном реально изменённом файле (T025 task file). Расширение BUG-DIFF-HANDOFF-BRANCH-SCOPE — баг системный для всех `M`-tracked файлов. **Фикс:** для diff-генерации использовать Edit tool call timestamps как scope boundary; для каждого файла генерировать `edit_snippet` из фактических Edit tool calls сессии вместо `git diff HEAD`; `git diff HEAD` оставить только fallback для файлов без Edit calls но с git-status изменением | P1 |
| BUG-ARTIFACTS-WORKING-TREE-M-REGR | Воспроизведено повторно в cc28aef9: `docs/ADV-HANDOFF.md` (modified) и `docs/ADV-architecture.md` (modified) попали в Artifacts — оба файла в git status M от предыдущих сессий, ни Read ни Edit на них в текущей сессии не было. Также `go.sum` (read) — не читался. Также `.claude/commands/codereview-local.md` (read) — не читался. Пересечение BUG-ARTIFACTS-WORKING-TREE-M и BUG-GLOB-AS-READ-REGRESSION. **Также воспроизведено в 440f2ed2:** T028, T045, T048, HANDOFF, architecture — все 5 файлов были в git status M до начала сессии (git status показан в IDE context), в сессии не трогались, попали в Artifacts и Diffs. **Также воспроизведено в f6500ac8:** ADV-T024 (deleted), T028, T045, T048, architecture — 5 файлов из git status предыдущей сессии попали в Artifacts и Diffs (в т.ч. полное удаление T024 ~140 строк). **Также воспроизведено в c21df815:** 9 файлов из git status M/D/?? попали в Artifacts (T024 deleted, T028/T045/T048/HANDOFF/architecture/CHANGELOG/config.go modified) — ни один не трогался в текущей сессии (только T025, artifacts.go, artifacts_test.go). При этом реально изменённые файлы (artifacts.go — 4 Edit-а, artifacts_test.go — 3 Edit-а) ОТСУТСТВУЮТ в Artifacts (они в `??` untracked status). **Также воспроизведено в c065e247:** 7 файлов из git status M/D попали в Artifacts и Diffs (T024 deleted, T028/T045/T048/CHANGELOG/HANDOFF/architecture modified) — в сессии трогали только T025 task file через Edit. **Также воспроизведено в 5b1c21f7 (ADV-T049 smoke test):** 15 phantom artifacts (adv binary, cmd/adv/main.go, 2 specs, 7 task files, CHANGELOG, HANDOFF, architecture, config.go) — всё из git status ветки codex/pipeline-hardening-stageb-finalize; в сессии трогали только T049 task file. Также ~2400 строк phantom git_head diffs из этих файлов, включая binary patch для `adv` бинарника. **Фикс:** тот же — artifact extractor должен пересекать файлы с tool calls текущей сессии | P1 |
| BUG-TASKS-PHANTOM-FROM-SKILL-EXAMPLES-REGR | Воспроизведено повторно в cc28aef9: T042 и T099 попали в Tasks — оба phantom из codereview.md skill template (примеры `T042, t042, 042` и `T099, JIRA-123`). T024 задублирован как ADV-T024 и T024. **Также воспроизведено в 440f2ed2:** T042 phantom из `/fix` skill template (skill обрабатывал T024, пример T042 из `/codereview` skill попал в tasks). T024 задублирован снова как ADV-T024+T024. **Также воспроизведено в c21df815:** T042 phantom из `/fix` skill prompt text — работали только с ADV-T025. **Также воспроизведено в 5b1c21f7 (ADV-T049 smoke test):** T001, T024, T032, T042, T048 — все фантомы из `/smoketest` skill template; T001 из примера "task T001 started", T032/T024/T048 из таблиц и примеров внутри шаблона. Работали только с T049. **Фикс:** тот же что SA-T049 — не извлекать task IDs из skill-файлов | P1 |
| BUG-SKILL-FALSE-POSITIVE-CODEREVIEW-REGR | Воспроизведено повторно в cc28aef9: `skill: codereview` и `skill: codereview-local` попали в теги — оба скилла НЕ вызывались через Skill tool. Codereview.md был только прочитан через Read tool для сравнения с smoketest. Одновременно `skill: smoketest` и `skill: autoresearch` (реально вызванные) отсутствовали. **Фикс:** skill tags ТОЛЬКО из Skill tool_use events | P1 |
| BUG-DIFFS-MISSING-OUTSIDE-REPO | Файлы вне git repo, изменённые через Edit tool, не попадают в Diffs. Воспроизведено в cc28aef9: `~/.claude/commands/smoketest.md` — 4 Edit calls (autoresearch), значительные правки — отсутствует и в Artifacts и в Diffs. Связан с BUG-ARTIFACTS-MISSING-OUTSIDE-REPO но касается также Diffs. **Фикс:** Edit tool calls к файлам вне cwd должны генерировать edit_snippet diff (из old_string/new_string параметров Edit tool call) | P1 |
| BUG-MODEL-SYNTHETIC-REGRESSION | `ai_model` записывается как `<synthetic>` вместо реального model ID (e.g., `claude-opus-4-6`). SA-T010 должен был это исправить, но баг воспроизвёлся в f6500ac8. Также `assistant` и `model` теги содержат `<synthetic>`. Видимо, парсер JSONL не может определить model из новых форматов JSONL или model field отсутствует в метаданных session. **Также воспроизведено в 5b1c21f7:** `claude-sonnet-4-6` вместо реального ID. **Фикс:** проверить логику определения модели в парсере; использовать model из JSONL метаданных или из `system` message; fallback на `claude-sonnet-4-6` | P1 |
| [SA-T062](3.%20tasks/SA-T062_bugfix_events-from-skill-template-content.md) | **Ложные события из шаблонов скиллов.** Воспроизведено в 5b1c21f7: `handoff_read` записан как event — реально HANDOFF.md не открывался. Источник: шаблон `/smoketest` содержит пример `- handoff_read` в секции Events, парсер принимает его за реальное событие. Механизм аналогичен BUG-TASKS-PHANTOM-FROM-SKILL-EXAMPLES но для Events. **Фикс:** игнорировать `<command-message>` content при event detection; детектировать `handoff_read` только из Read tool calls на `HANDOFF*.md` | P1 |
| BUG-TASKS-EMPTY-WHEN-REAL | Tasks секция пуста при наличии реальной работы с задачей. Воспроизведено в f6500ac8: работали с ADV-T025 (Read task file, implement, tests), но Tasks пуста. Парсер не извлёк task ID из Read tool call на task file или из TodoWrite items. Может быть связан с SA-T051 (tasks empty when skill invoked). **Фикс:** извлекать task IDs из: (1) Read tool calls на файлы содержащие task IDs в имени (ADV-T025_*.md), (2) TodoWrite items содержащие task references, (3) summary text (regex `ADV-T\d+`) | P1 |
| BUG-WRITE-SNAPSHOT-STALE-DIFF | Write tool создаёт `write_snapshot` diff с исходным контентом файла. Если файл потом правится через Edit, write_snapshot остаётся стейл — показывает первую версию, а Edit дифы показывают дельту. В f6500ac8: `artifacts.go` write_snapshot содержит `defer in.Close()` (без errcheck), а отдельный edit diff уже показывает `defer func() { _ = in.Close() }()`. Корректно по отдельности, но сбивает с толку при чтении — непонятно какая версия финальная. **Рекомендация:** либо (a) пометить write_snapshot как `(initial version, see edits below)`, либо (b) для Write+Edit на один файл генерировать только финальный diff | P2 |
| BUG-SYNTHETIC-DIFF-ABSOLUTE-PATH | Synthetic diff для Write tool использует абсолютный путь в `---`/`+++` headers вместо относительного. Воспроизведено в f6500ac8: `--- a/Users/is/personal/Projects/09_AutoDev_v2/internal/artifacts/artifacts.go` вместо `--- a/internal/artifacts/artifacts.go`. Для git_head diffs пути корректные (относительные). **Фикс:** в synthetic diff генераторе нормализовать пути относительно project root | P2 |
| BUG-TOOL-CALL-COUNT-WRONG | `tool_call_count` в SQLite записывается как 1 при реальных 32+ tool calls. Воспроизведено в c21df815: session с 32 tool_use вызовами (Read, Edit, Bash, Grep, Glob, Write, Skill) — tool_call_count=1. Парсер видимо считает только tool calls определённого типа или только первый. **Фикс:** парсер должен считать ВСЕ `tool_use` content blocks в assistant messages, включая Read, Edit, Bash, Grep, Glob, Write, Skill | P1 |
| BUG-OPEN-ISSUES-REGRESSION | `open_issues` содержит фрагмент assistant response text вместо реальных open issues. SA-T016 зафиксил BUG-OPEN-ISSUES-CONTENT, но регрессировал. Воспроизведено в c065e247: `open_issues = ["Let me verify the remaining open findings from previous reviews."]` — это предложение из assistant response, не issue. Реальные open issues (2x MEDIUM: DetectNewIssuesCount ScriptRunner bypass, malformed review = clean) не захвачены. **Фикс:** open_issues extractor должен использовать evidence-based подход (парсить секции "Находки" из task file edits или явные TODO/OPEN маркеры), не text heuristics из assistant prose | P1 |
| BUG-EVENTS-FROM-GIT-STATUS | Event detector generates `spec_read` and `handoff_read` events from phantom artifacts (git status M/D files, subagent reads) without verifying actual Read tool calls in the main session. Воспроизведено в 612c826c: `spec_read` event generated because spec file appeared in artifacts (read by Explore subagent, not main session); `handoff_read` event generated because HANDOFF.md was in git status M artifacts. Neither file was Read-tooled in the main session. **Фикс:** event detector должен проверять что artifact action=read подтверждён реальным Read tool call в main session (не субагент), а не просто наличием в session_artifacts | P1 |
| BUG-SKILL-TAG-SMOKETEST-MISSING | `skill: smoketest` тег не попадает в session_tags несмотря на реальный Skill tool call `skill: "smoketest"`. Воспроизведено в 612c826c: Skill tool вызван с `skill: "smoketest"`, тег отсутствует; при этом phantom `skill: codereview` присутствует (из text match). Аналогичен BUG-SKILL-TAG-ARCHIVE-SESSION-MISSING — скилл без дефиса тоже не детектируется. **Фикс:** skill tag extractor должен парсить `skill` parameter из Skill tool_use calls | P1 |
| BUG-ARTIFACTS-UNTRACKED-NOT-CAPTURED | Файлы в `??` (untracked) git status, изменённые через Edit tool, не попадают в Artifacts и Diffs. Воспроизведено в c21df815: `internal/artifacts/artifacts.go` и `artifacts_test.go` (директория `internal/artifacts/` в `??` status) — 7 Edit calls суммарно, ни один не попал в artifacts/diffs. Экспорт содержит только `git_head` diffs для tracked M/D файлов. **Фикс:** artifact extractor должен создавать записи из Edit/Write tool calls независимо от git status; для untracked файлов генерировать edit_snippet diff из old_string/new_string параметров | P1 |
| BUG-SUMMARY-NOT-UPDATED-ON-RERUN | `archive-current --summary "..."` не обновляет `summary` и `summary_manual` если `summary_manual` уже непусто, даже при `manually_reviewed=0`. Воспроизведено в 2c2aa57e: JSONL содержит несколько сессий; первый `archive-current` записал summary от предыдущей сессии; повторный запуск с правильным `--summary` → в SQLite по-прежнему старый summary. Расширение BUG-SUMMARY-MANUAL-BLOCKS-RERUN: при multi-session JSONL первая архивация захватывает чужой summary, а вторая не может его исправить. **Фикс:** `archive-current` с явным `--summary` всегда должен обновлять summary/summary_manual когда `manually_reviewed ≠ 1` | P1 |
| BUG-TASKS-PHANTOM-SKILL-TEST-IDS | Task IDs из mock/test кода в файлах прочитанных через Read tool попадают в session_tasks. Воспроизведено в 2c2aa57e: `T099` появился из `handoff_sync_test.go` (mock task ID "ADV-T099"); `T042` — phantom из codereview skill template. **Фикс:** не извлекать task IDs из `_test.go` файлов и skill template expansions | P1 |
| BUG-TASKS-EMPTY-SKILL-NEXT | Tasks пуст при работе с задачей через `/next` скилл. Воспроизведено в 8929c02d: вызван `/next`, реализована ADV-T028 (Read task file + Write 3 файлов + Edit executor.go + go test), Tasks = []. Аналогичен BUG-TASKS-EMPTY-WHEN-REAL и SA-T051, но специфично для сценария Skill(next) + Write tool (untracked файлы). Парсер не извлекает task ID ни из имени Read'd task file, ни из Write calls. **Фикс:** извлекать task_id из Read tool calls на файлы с паттерном `ADV-T\d+_*.md` в имени; аналогично для Write calls | P1 |
| BUG-ARTIFACTS-GIT-STATUS-REGR-8929c02d | Воспроизведено повторно в 8929c02d (ADV-T028): 3 phantom artifacts из git status ветки `codex/pipeline-hardening-stageb-finalize` — `ADV-S05 spec` (modified), `ADV-T049` (deleted), `handoff_sync.go` (modified) — все три были в `git status M/D` до начала сессии, ни один не трогался через Read/Edit/Write. BUG-ARTIFACTS-WORKING-TREE-M-REGR воспроизводится стабильно на этой ветке с каждой сессией. Также: 3 соответствующих фантомных diff-секции (~370 строк) в Diffs. **Также воспроизведено в 4065ce28 (2026-04-12):** 13 phantom artifacts (plan_spec_critic.md, main.go, plan_test.go, 2 specs, T045 deleted, T034 deleted, CHANGELOG, HANDOFF, findings_test.go, writer.go, mock_executor.go, parity_test.go) + 1300+ строк phantom diffs; в сессии трогали только HANDOFF.md (Edit) и T057 (Write, untracked). **Также воспроизведено в 4a33b88b (2026-04-14, ADV-T029 deep review):** ~40 phantom artifacts (adv binary, cmd/adv/main.go, main_test.go, 2 specs, T026/T027 deleted, T029/T031/T036/T037-T044/T047/T055/T056 tasks, guides, HANDOFF, dag.go, state.go, scheduler files, runner files, worktree.go, parity_test.go) + T036 code review diff (~150 строк) + adv binary diff (~5000 строк). Сессия трогала ТОЛЬКО T029 task file (Edit). **Счётчик:** 12+ воспроизведений. Критически мешает читаемости архива. | P0 |
| BUG-HANDOFF-READ-EVENT-MISSING | `handoff_read` event не генерируется несмотря на реальный Read tool call на `docs/ADV-HANDOFF.md`. Воспроизведено в 8929c02d: первый tool call в сессии — Read ADV-HANDOFF.md + ADV-CHANGELOG.md; `changelog_read` сгенерирован, `handoff_read` — нет. Вероятная причина: HANDOFF.md попал в artifacts как `(modified)` через git status, event detector проверяет `action=read` для `handoff_read`, но видит `modified`. **Фикс:** event detector должен детектировать `handoff_read` из Read tool calls напрямую, независимо от artifact action | P2 |
| BUG-TOOL-IDS-IGNORED-WRONG-SESSION | `--tool-ids` передан но скрипт захватил чужую сессию. Воспроизведено в d50a9199: `ls -t` выбрал `e0cc34bd` (smoketest, 79 строк) вместо `d50a9199` (codereview, правильная). `--tool-ids` содержал 22 корректных ID из текущей сессии, но tool-ids фильтр НЕ использовался для выбора JSONL-файла — он применяется только к содержимому уже выбранного JSONL. Скрипт не проверил что ни один из tool-ids не присутствует в выбранном файле. **Фикс:** при наличии `--tool-ids` скрипт должен: (1) перебрать топ-N JSONL по mtime, (2) для каждого grep первый tool-id из списка, (3) выбрать файл с совпадением. Если ни один не содержит tool-ids → fail с сообщением | P0 |
| BUG-TASKS-PHANTOM-CODEREVIEW-TEMPLATE-REGR | Task IDs T042 и T099 из codereview skill template продолжают попадать в session_tasks. Воспроизведено в d50a9199: T042 (action=mentioned), T046 (action=reviewed — ложный, T046 только упомянут в scope как dependency), T099 (action=implemented — абсурдный, T099 из примера "T099, JIRA-123" в codereview template). Расширение BUG-TASKS-PHANTOM-FROM-SKILL-EXAMPLES. **Также воспроизведено в 4a33b88b (2026-04-14, ADV-T029 deep review):** ADV-T036, T036, T042, T046, T099 — все phantom. Работали ТОЛЬКО с ADV-T029. T036 из предыдущей сессии в том же JSONL, T042/T099 из skill templates, T046 из прочитанного HANDOFF context. **Фикс:** тот же — не извлекать task IDs из content внутри `<command-message>`/`<command-name>` блоков (skill template expansions) | P1 |
| BUG-EVENTS-CODE-REVIEW-NOT-DETECTED | Нет события `code_review_completed` для сессии целиком посвящённой code review. Воспроизведено в d50a9199: вся сессия — /codereview T026, результат записан Edit-ом в task file с секцией "## Code Review", но events = [session_archived]. **Фикс:** детектировать `code_review_completed` из: (1) Skill tool call с `skill: "codereview"`, (2) Edit tool call добавляющий секцию "## Code Review" в task file | P2 |
| BUG-DIFF-SMOKETEST-SECTION-CROSS-SESSION | Diff содержит изменения из предыдущей сессии, записанные в тот же файл. Воспроизведено в d50a9199: diff для T026 task file включает секцию "## Smoke Test (independent) — 2026-04-13 21:30" (~60 строк) записанную предыдущей smoketest-сессией (e0cc34bd). Текущая сессия добавила только "## Code Review — 2026-04-13 23:00". Источник: `git diff HEAD` показывает ВСЕ незакоммиченные изменения файла, включая правки других сессий. Частный случай BUG-DIFF-ALL-WORKING-TREE для сценария когда 2 сессии правят один файл. **Фикс:** использовать Edit tool calls (old_string/new_string) для генерации edit_snippet diff вместо git diff HEAD | P1 |

### Приоритет 1: Стабильность
- ~~**[SA-T004](3.%20tasks/Done/SA-T004_bugfix_events-detection_done.md)**~~ — ~~Events phantom/missing: BUG-31, BUG-EVENTS-FALSE-POSITIVE, BUG-EVENTS-MISSING (25+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T005](3.%20tasks/Done/SA-T005_bugfix_slug-query-commit_done.md)**~~ — ~~PROJECT_SLUG leading dash + cmd_query без commit~~ ✅ done 2026-04-03
- ~~**[SA-T006](3.%20tasks/Done/SA-T006_bugfix_tasks-summary-context-drift_done.md)**~~ — ~~Tasks/Summary дрейф из контекста (BUG-27/39/17, 49+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T007](3.%20tasks/Done/SA-T007_bugfix_artifacts-bash-mv-rm_done.md)**~~ — ~~Artifacts: mv/rm через Bash (BUG-NEW, 15+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T008](3.%20tasks/Done/SA-T008_bugfix_domain-context-drift_done.md)**~~ — ~~Domain-теги из текста диалога (BUG-TAGS-CONTEXT-DRIFT, 13+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T009](3.%20tasks/Done/SA-T009_bugfix_diff-full-file-synthetic_done.md)**~~ — ~~Diff: весь файл как новый для untracked (BUG-DIFF-SCOPE, 19+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T010](3.%20tasks/Done/SA-T010_bugfix_assistant-tag-model-id_done.md)**~~ — ~~Model ID захардкожен как "claude" (BUG-ASSISTANT-TAG-VALUE, 5+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T011](3.%20tasks/Done/SA-T011_bugfix_archive-integrity_done.md)**~~ — ~~Archive overwrite guard: summary_manual + mtime precision + session_id check (9+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T012](3.%20tasks/Done/SA-T012_bugfix_phantom-skill-tags_done.md)**~~ — ~~Phantom skill-теги: XML-маркеры и prose вместо Skill tool calls (8+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T013](3.%20tasks/Done/SA-T013_bugfix_message-duplicates_done.md)**~~ — ~~Дубли сообщений: дедупликация перед записью в SQLite и MD (7+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T014](3.%20tasks/Done/SA-T014_bugfix_tasks-from-tool-results_done.md)**~~ — ~~Task IDs из tool results: T042 появился в tasks из содержимого прочитанных файлов~~ ✅ done 2026-04-03
- ~~**[SA-T015](3.%20tasks/Done/SA-T015_bugfix_artifact-write-action_done.md)**~~ — ~~Write на tracked файл → action=created вместо modified~~ ✅ done 2026-04-03
- ~~**[SA-T016](3.%20tasks/SA-T016_bugfix_open-issues-content.md)**~~ — ~~Open Issues stdout/reasoning-текст~~ ✅ done 2026-04-03
- ~~**[SA-T017](3.%20tasks/Done/SA-T017_bugfix_artifacts-phantom-context_done.md)**~~ — ~~Фантомные артефакты из соседних сессий (4+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T018](3.%20tasks/Done/SA-T018_bugfix_artifacts-missing-and-diffs_done.md)**~~ — ~~Пропущенные артефакты и дифы (6+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T019](3.%20tasks/SA-T019_bugfix_pseudo-artifacts-events.md)**~~ — ~~Pseudo-artifacts event:* в session_artifacts~~ ✅ done 2026-04-03
- ~~**[SA-T020](3.%20tasks/SA-T020_bugfix_skill-tags-detection.md)**~~ — ~~Skill-теги: missing + timing boundary~~ ✅ done 2026-04-03
- ~~**[SA-T021](3.%20tasks/Done/SA-T021_bugfix_synthetic-diff-format_done.md)**~~ — ~~Synthetic diff: пустые строки + full-file add для modified untracked (21+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T022](3.%20tasks/SA-T022_bugfix_artifact-operation-classification.md)**~~ — ~~Artifact ops: A+D collapse, cwd-фильтр, failed-edit, mv tracking~~ ✅ done 2026-04-03
- ~~**[SA-T023](3.%20tasks/Done/SA-T023_bugfix_jsonl-integrity_done.md)**~~ — ~~JSONL integrity: float mtime + UNIQUE constraints~~ ✅ done 2026-04-03
- ~~**[SA-T024](3.%20tasks/Done/SA-T024_bugfix_skill-detection-command-message_done.md)**~~ — ~~Skill detection из command-message тегов~~ ✅ done 2026-04-03
- ~~**[SA-T025](3.%20tasks/Done/SA-T025_bugfix_slug-underscore-to-dash_done.md)**~~ — ~~PROJECT_SLUG underscore→dash~~ ✅ done 2026-04-03
- ~~**[SA-T026](3.%20tasks/Done/SA-T026_bugfix_summary-accuracy_done.md)**~~ — ~~Summary accuracy: archive-boundary (5+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T027](3.%20tasks/Done/SA-T027_bugfix_bash-parsing-fixes_done.md)**~~ — ~~Bash parsing: shell vars + task IDs + diff dedup~~ ✅ done 2026-04-03
- ~~**[SA-T028](3.%20tasks/Done/SA-T028_bugfix_artifact-noise-reduction_done.md)**~~ — ~~Artifact noise reduction: ide/glob/skill-examples~~ ✅ done 2026-04-03
- ~~**[SA-T029](3.%20tasks/Done/SA-T029_arch_evidence-based-extraction_done.md)**~~ — ~~**Архитектура:** Evidence-based extraction layer (recurring)~~ ✅ done 2026-04-03
- ~~**[SA-T030](3.%20tasks/Done/SA-T030_bugfix_regression-integrity_done.md)**~~ — ~~Регрессии: overwrite guard, msg-dedup, open_issues fmt~~ ✅ done 2026-04-03
- ~~**[SA-T031](3.%20tasks/Done/SA-T031_bugfix_artifact-session-lifecycle_done.md)**~~ — ~~Artifact lifecycle: created+deleted, multi-commit diff~~ ✅ done 2026-04-03
- ~~**[SA-T032](3.%20tasks/Done/SA-T032_bugfix_summary-from-context_done.md)**~~ — ~~Summary из контекста вместо outcome (3+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T033](3.%20tasks/Done/SA-T033_bugfix_shell-read-trace_done.md)**~~ — ~~Artifacts: bash shell-read trace пропадает (3+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T034](3.%20tasks/Done/SA-T034_bugfix_artifacts-wrong-session_done.md)**~~ — ~~Artifacts: файлы из предыдущей сессии (2+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T035](3.%20tasks/Done/SA-T035_bugfix_diff-synthetic-modified_done.md)**~~ — ~~Diff: whole-file для modified untracked + wrong-file (2+ сессий)~~ ✅ done 2026-04-03
- ~~**[SA-T036](3.%20tasks/Done/SA-T036_bugfix_rerun-overwrite-regressions_done.md)**~~ — ~~archive-current re-run уничтожает ручные правки + регрессии~~ ✅ done 2026-04-03
- ~~**[SA-T037](3.%20tasks/Done/SA-T037_s01_context-window-whitelist_done.md)**~~ — ~~Реализовать SA-S01: context-window whitelist для session boundary (`--tool-ids` в archive-current + обновление скилла)~~ ✅ done 2026-04-03
- Проверить и удалить `session_archive.backup.2026-03-27.py` если всё работает корректно
- Добавить тест на парсинг Claude JSONL (регрессионный)

### Приоритет 2: Аналитика
- Улучшить `analyze.py deep`: добавить граф зависимостей задач
- Отчёт: сколько времени тратится на каждый проект (по датам)
- Экспорт в CSV для анализа в spreadsheets

### Приоритет 3: UX
- `/verify-archive` — проверка последней записанной сессии на корректность
- Дашборд в терминале (rich/textual) без Datasette

### Приоритет 4: Фичи
- Поиск по тексту сессий в legacy CLI/SQLite — опционально, если browser search из SA-S03 окажется недостаточным
- Тег-система: ручная разметка сессий
- Экспорт конкретной сессии по ID

### Приоритет 5: Browser-first app (draft)

- **[SA-S02](2.%20specifications/SA-S02_browser_app_foundation.md)** — Rails browser shell + PostgreSQL read model
  1. **[SA-T038](3.%20tasks/SA-T038_s02_rails_app_shell.md)** — Rails app shell и базовая инфраструктура
     - **Блокирует:** SA-T039, SA-T040, SA-T041
  2. **[SA-T039](3.%20tasks/SA-T039_s02_sqlite_to_postgres_sync.md)** — идемпотентный sync SQLite архива в PostgreSQL
     - **Требует:** SA-T038
     - **Блокирует:** SA-T040, SA-T041
  3. **[SA-T040](3.%20tasks/SA-T040_s02_sessions_index.md)** — каталог сессий в браузере
     - **Требует:** SA-T039
  4. **[SA-T041](3.%20tasks/SA-T041_s02_session_detail_readonly.md)** — read-only карточка сессии
     - **Требует:** SA-T039
     - **Можно параллельно с:** SA-T040

- **[SA-S03](2.%20specifications/SA-S03_review_and_operations_workspace.md)** — review, поиск и operations workspace
  1. **[SA-T042](3.%20tasks/SA-T042_s03_review_queue_and_status.md)** — review queue и triage-статусы
     - **Требует:** SA-S02
     - **Блокирует:** SA-T043, SA-T044, SA-T045
  2. **[SA-T043](3.%20tasks/SA-T043_s03_manual_summary_curation.md)** — ручная курация summary и open issues
     - **Требует:** SA-T042
  3. **[SA-T044](3.%20tasks/SA-T044_s03_search_and_saved_views.md)** — поиск по архиву и saved views
     - **Требует:** SA-T042
     - **Можно параллельно с:** SA-T043
  4. **[SA-T045](3.%20tasks/SA-T045_s03_sync_and_rebuild_operations.md)** — operations page для sync и rebuild
     - **Требует:** SA-T042
     - **Можно параллельно с:** SA-T043, SA-T044

---

## Как запустить

```bash
# Сохранить текущую сессию
/archive-session   # в Claude Code чате

# Статистика
python3 analyze.py
python3 analyze.py summary
python3 analyze.py deep autodev-v2

# Веб-интерфейс
pip install datasette
datasette data/sessions.db

# Прямой SQL
python3 session_archive.py query "SELECT repo_name, COUNT(*) FROM sessions GROUP BY repo_name"
```

---

## Ключевые файлы для нового контекста

| Файл | Зачем читать |
|------|-------------|
| [SA-architecture.md](SA-architecture.md) | Полная техническая картина |
| [README.md](../README.md) | Быстрый старт и примеры |
| [BUGS.md](../BUGS.md) | Известные проблемы |
| [session_archive.py](../session_archive.py) | Основной CLI (парсинг, БД) |
| [analyze.py](../analyze.py) | Аналитические отчёты |

---

## Правила для AI-ассистентов

- **НЕ трогать `data/`** без явной команды — там живые данные
- **`session_archive.backup.2026-03-27.py`** — не удалять без проверки
- **Схема эволюции через `_ensure_column()`** — не писать SQL миграции вручную
- **Нет внешних зависимостей** в `session_archive.py` — только stdlib Python 3
- При добавлении новых колонок — добавлять через `_ensure_column()` в `_init_schema()`
- Экспортный путь строится как: `YYYY-MM-DD_reponame_agentfamily_hash8.md`
