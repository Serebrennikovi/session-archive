# Известные баги и ручные исправления архива

## Трекинг повторяющихся багов → задачи

| Баг | Задача | Статус |
|-----|--------|--------|
| BUG-34 (model всегда `claude`) | [SA-T001](docs/3.%20tasks/Done/SA-T001_bugfix_parser-model-tags_done.md) | ✅ fixed |
| BUG-TAGS-XML-MARKERS, BUG-TAGS-GARBAGE-SKILLS | [SA-T001](docs/3.%20tasks/Done/SA-T001_bugfix_parser-model-tags_done.md) | ✅ fixed |
| BUG-TAGS-CONTEXT-DRIFT (domain) | [SA-T008](docs/3.%20tasks/Done/SA-T008_bugfix_domain-context-drift_done.md) | ✅ fixed |
| BUG-TASKS-FALSE-POSITIVE | [SA-T003](docs/3.%20tasks/Done/SA-T003_bugfix_tasks-false-positive_done.md) | ✅ fixed |
| BUG-DIFF-EMPTY-LINES, BUG-DIFF-DOUBLE-SLASH, BUG-DIFF-UNTRACKED-SCOPE | [SA-T002](docs/3.%20tasks/Done/SA-T002_bugfix_diff-formatting_done.md) | ✅ fixed |
| BUG-PROJECT-SLUG-MISMATCH, BUG-SLUG-LEADING-DASH, BUG-42, BUG-04, BUG-20 | [SA-T005](docs/3.%20tasks/Done/SA-T005_bugfix_slug-query-commit_done.md) | ✅ fixed |
| BUG-31, BUG-EVENTS-FALSE-POSITIVE, BUG-EVENTS-MISSING, BUG-EVENTS-PHANTOM | [SA-T004](docs/3.%20tasks/SA-T004_bugfix_events-detection.md) | ✅ fixed |
| BUG-QUERY-NO-COMMIT | [SA-T005](docs/3.%20tasks/Done/SA-T005_bugfix_slug-query-commit_done.md) | ✅ fixed |
| BUG-SLUG-UNDERSCORE-TO-DASH | [SA-T025](docs/3.%20tasks/Done/SA-T025_bugfix_slug-underscore-to-dash_done.md) | ✅ fixed |
| BUG-PARALLEL-SESSION-OVERWRITE | [SA-T029](docs/3.%20tasks/SA-T029_arch_evidence-based-extraction.md) | ✅ fixed (sessionId filter in parser) |
| BUG-DIFF-PARALLEL-SESSION | [SA-T029](docs/3.%20tasks/SA-T029_arch_evidence-based-extraction.md) | ✅ fixed (archive_boundary + sessionId) |
| BUG-ARTIFACTS-GLOB-VS-READ | [SA-T028](docs/3.%20tasks/Done/SA-T028_bugfix_artifact-noise-reduction_done.md) | ✅ fixed |
| BUG-DIFF-FULL-FILE-UNTRACKED, BUG-DIFF-SCOPE, BUG-DIFF-WRONG-HUNK | [SA-T009](docs/3.%20tasks/Done/SA-T009_bugfix_diff-full-file-synthetic_done.md) | ✅ fixed |
| BUG-TAGS-DOMAIN-DATABASE-FALSE | [SA-T029](docs/3.%20tasks/SA-T029_arch_evidence-based-extraction.md) | ✅ fixed |
| BUG-ASSISTANT-TAG-VALUE | [SA-T010](docs/3.%20tasks/Done/SA-T010_bugfix_assistant-tag-model-id_done.md) | ✅ fixed |
| BUG-27, BUG-39, BUG-17, BUG-TASKS, BUG-TASKS-FROM-CONTEXT | [SA-T006](docs/3.%20tasks/Done/SA-T006_bugfix_tasks-summary-context-drift_done.md) | ✅ fixed |
| BUG-NEW, BUG-ARTIFACTS-WRONG-ACTION | [SA-T007](docs/3.%20tasks/Done/SA-T007_bugfix_artifacts-bash-mv-rm_done.md) | ✅ fixed |
| BUG-MV-RM-PYTHON-ARGS, BUG-MV-RM-QUOTED-PATHS, BUG-MV-RM-SUMMARY-ARGS | — | open |
| BUG-TAGS-SKILL-CONFIG-FILE | — | open |
| BUG-OPEN-ISSUES-REASONING-TEXT | [SA-T016](docs/3.%20tasks/Done/SA-T016_bugfix_open-issues-content_done.md) | ✅ fixed |
| BUG-ARTIFACTS-IDE-OPEN-AS-READ | — | open |
| BUG-ARTIFACTS-PHANTOM-CONTEXT | [SA-T017](docs/3.%20tasks/Done/SA-T017_bugfix_artifacts-phantom-context_done.md) | ✅ fixed |
| BUG-DIFF-MISSING-TRACKED-FILES | [SA-T018](docs/3.%20tasks/Done/SA-T018_bugfix_artifacts-missing-and-diffs_done.md) | ✅ fixed |
| BUG-TASKS-FALSE-POSITIVE-SKILL-EXAMPLE | — | open |
| BUG-TASKS-FROM-TOOL-RESULTS | [SA-T014](docs/3.%20tasks/Done/SA-T014_bugfix_tasks-from-tool-results_done.md) | ✅ fixed |
| BUG-ARTIFACTS-WRITE-ACTION | [SA-T015](docs/3.%20tasks/Done/SA-T015_bugfix_artifact-write-action_done.md) | ✅ fixed |
| BUG-ARTIFACTS-MISSING, BUG-DIFF-MISSING-TRACKED-FILES | [SA-T018](docs/3.%20tasks/Done/SA-T018_bugfix_artifacts-missing-and-diffs_done.md) | ✅ fixed |
| BUG-SUMMARY-PARTIAL | — | open |
| BUG-OPEN-ISSUES-CONTENT, BUG-OPEN-ISSUES-REASONING-TEXT | [SA-T016](docs/3.%20tasks/Done/SA-T016_bugfix_open-issues-content_done.md) | ✅ fixed |
| BUG-TASKS-ID-NO-PREFIX | — | open |
| BUG-24, BUG-22, BUG-41 | [SA-T019](docs/3.%20tasks/Done/SA-T019_bugfix_pseudo-artifacts-events_done.md) | ✅ fixed |
| BUG-SKILL-MISSING, BUG-SKILL-TIMING | [SA-T020](docs/3.%20tasks/Done/SA-T020_bugfix_skill-tags-detection_done.md) | ✅ fixed |
| BUG-40, BUG-DIFF-FMT, BUG-12 | [SA-T021](docs/3.%20tasks/SA-T021_bugfix_synthetic-diff-format.md) | draft |
| BUG-DOMAIN-CONTEXT | — | closed (root cause — phantom artifacts, покрыто T017+T019) |
| BUG-ARTIFACT-WRONG-OP, BUG-ARTIFACT-MISSING-MOVE, BUG-ARTIFACTS-OUTSIDE-CWD, BUG-DIFF-FAILED-EDIT-CAPTURED | [SA-T022](docs/3.%20tasks/Done/SA-T022_bugfix_artifact-operation-classification_done.md) | ✅ fixed |
| BUG-TAGS-SKILL-MISSING | — | open |
| BUG-ARCHIVE-OVERWRITE, BUG-SUMMARY-REGENERATE, BUG-DIFF-WRONG-SESSION | [SA-T011](docs/3.%20tasks/Done/SA-T011_bugfix_archive-integrity_done.md) | ✅ fixed |
| BUG-SKILL-XML, BUG-SKILL-PHANTOM | [SA-T012](docs/3.%20tasks/Done/SA-T012_bugfix_phantom-skill-tags_done.md) | ✅ fixed |
| BUG-14, BUG-21 (дубли сообщений) | [SA-T013](docs/3.%20tasks/Done/SA-T013_bugfix_message-duplicates_done.md) | ✅ fixed |
| BUG-SHELL-VAR-AS-PATH | [SA-T027](docs/3.%20tasks/Done/SA-T027_bugfix_bash-parsing-fixes_done.md) | ✅ fixed |
| BUG-TASK-IDS-BASH-MOVE | [SA-T027](docs/3.%20tasks/Done/SA-T027_bugfix_bash-parsing-fixes_done.md) | ✅ fixed |
| BUG-SKILL-TAGS-SLASH-COMMAND | [SA-T024](docs/3.%20tasks/Done/SA-T024_bugfix_skill-detection-command-message_done.md) | ✅ fixed |
| BUG-WRONG-JSONL, BUG-JSONL-MTIME, BUG-SQLITE-NO-UNIQUE-CONSTRAINT | [SA-T023](docs/3.%20tasks/Done/SA-T023_bugfix_jsonl-integrity_done.md) | ✅ fixed |
| BUG-SLUG-UNDERSCORE-TO-DASH | [SA-T025](docs/3.%20tasks/Done/SA-T025_bugfix_slug-underscore-to-dash_done.md) | ✅ fixed |
| BUG-SUMMARY-MISMATCH, BUG-SUMMARY-CONTEXT-DRIFT, BUG-SUMMARY-MIXED-PHASES, BUG-SUMMARY-PARTIAL | [SA-T026](docs/3.%20tasks/Done/SA-T026_bugfix_summary-accuracy_done.md) | ✅ fixed |
| BUG-MV-RM-PYTHON-ARGS, BUG-MV-RM-QUOTED-PATHS, BUG-MV-RM-SUMMARY-ARGS, BUG-DIFF-DUPLICATE | [SA-T027](docs/3.%20tasks/Done/SA-T027_bugfix_bash-parsing-fixes_done.md) | ✅ fixed |
| BUG-TAGS-SKILL-MISSING | [SA-T024](docs/3.%20tasks/Done/SA-T024_bugfix_skill-detection-command-message_done.md) | ✅ fixed |
| BUG-ARTIFACTS-IDE-OPEN-AS-READ, BUG-ARTIFACTS-GLOB-VS-READ, BUG-TASKS-FALSE-POSITIVE-SKILL-EXAMPLE, BUG-TAGS-SKILL-CONFIG-FILE, BUG-TASKS-ID-NO-PREFIX | [SA-T028](docs/3.%20tasks/Done/SA-T028_bugfix_artifact-noise-reduction_done.md) | ✅ fixed |
| BUG-TAGS-DOMAIN-DATABASE-FALSE, BUG-PARALLEL-SESSION-OVERWRITE, BUG-DIFF-PARALLEL-SESSION, BUG-EVENTS-FALSE-POSITIVE (recurring) | [SA-T029](docs/3.%20tasks/SA-T029_arch_evidence-based-extraction.md) | ✅ fixed |
| BUG-ARCHIVE-OVERWRITE (regression), BUG-MSG-DEDUP-REGRESSION, BUG-OPEN-ISSUES-FMT | [SA-T030](docs/3.%20tasks/Done/SA-T030_bugfix_regression-integrity_done.md) | ✅ fixed |
| BUG-40, BUG-DIFF-FMT, BUG-12 | [SA-T021](docs/3.%20tasks/Done/SA-T021_bugfix_synthetic-diff-format_done.md) | ✅ fixed |
| BUG-SUMMARY-MISMATCH, BUG-SUMMARY-MIXED-PHASES | [SA-T026](docs/3.%20tasks/Done/SA-T026_bugfix_summary-accuracy_done.md) | ✅ fixed |
| BUG-WRONG-SESSION-ARCHIVE | — | open |
| BUG-ARTIFACT-DELETED, BUG-DIFF-SPLIT | [SA-T031](docs/3.%20tasks/Done/SA-T031_bugfix_artifact-session-lifecycle_done.md) | ✅ fixed |
| BUG-SUMMARY-FROM-CONTEXT | [SA-T032](docs/3.%20tasks/Done/SA-T032_bugfix_summary-from-context_done.md) | ✅ fixed |
| BUG-ARTIFACTS-PARTIAL, BUG-ARTIFACTS-EMPTY | [SA-T033](docs/3.%20tasks/Done/SA-T033_bugfix_shell-read-trace_done.md) | ✅ fixed |
| BUG-ARTIFACTS-WRONG-SESSION | [SA-T034](docs/3.%20tasks/Done/SA-T034_bugfix_artifacts-wrong-session_done.md) | ✅ fixed |
| BUG-DIFF-SYNTHETIC, BUG-DIFF-WRONG-FILE | [SA-T035](docs/3.%20tasks/Done/SA-T035_bugfix_diff-synthetic-modified_done.md) | ✅ fixed |
| BUG-RERUN-OVERWRITE, BUG-ARTIFACT-ACTION-WRONG, BUG-ARTIFACT-EVENT-PSEUDO | [SA-T036](docs/3.%20tasks/Done/SA-T036_bugfix_rerun-overwrite-regressions_done.md) | ✅ fixed |
| BUG-DUPLICATE-DELETED-MOVED | — | open |
| BUG-MV-RELATIVE-PATH | — | open |
| BUG-HANDOFF-DIFF-MULTI-SESSION | — | open |
| BUG-MV-QUOTED-PATHS-WITH-SPACES | — | open |
| BUG-EVENTS-LITERAL-STRINGS | — | open |
| BUG-RERUN-OVERWRITE-DURING-VERIFY | — | open |
| BUG-SUMMARY-WRONG-SESSION-ON-RERUN | — | open |
| BUG-ARTIFACTS-OUTSIDE-CWD-MISSING | — | open |
| BUG-JSONL-CROSS-SESSION-REGRESSION | — | open |
| BUG-SUMMARY-CONTEXT-SPANS-SESSIONS | — | open |
| BUG-MANUALLY-REVIEWED-BLOCKS-RERUN | — | ✅ fixed (summary updates even in manually_reviewed early-exit path when --summary is explicit) |
| BUG-UNIQUE-INDEX-SILENT-FAIL | — | ✅ fixed (dedup guard added for tags/tasks/events before UNIQUE index creation) |
| BUG-ARTIFACT-EPHEMERAL-CROSS-SESSION | — | open |
| BUG-HANDOFF-READ-OVERWRITE | — | open |
| BUG-EXPORT-DB-DESYNC | — | open |

> Описание root cause и план фикса — в задаче SA-T001.
> Ниже — лог ручных правок по сессиям (история).

---

## Сессия 2026-04-03_12-SessionArchive_claude_2a640d04 — SA-T023..T025/T027/T028 + verify

**Сессия:** `2a640d04-23f0-423c-b972-c685fa4969fb`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /intro → реализация SA-T023/T024/T025/T027/T028 → /accept → /archive-session → /verify-archive.

**Найденные проблемы:**

- **BUG-MANUALLY-REVIEWED-BLOCKS-RERUN** (подтверждён): session_id `2a640d04` ранее был заархивирован и `manually_reviewed=1` выставлен предыдущим verify-archive. При повторном `archive-current --summary "..."` — `write_session` берёт early-exit path, обновляет только counts. Результат: summary, tags, tasks, artifacts в SQLite остались от предыдущей сессии (bugs-to-task). Export .md был записан с данными из метаданных нового запуска (msg_count=26 правильный, но summary из metadata = новый), однако summary в export оказался старым из-за BUG-SUMMARY-WRONG-SESSION-ON-RERUN. Root cause: SA-T036 добавил `manually_reviewed` guard который слишком агрессивен — не позволяет даже явному `--summary` пробиться. Fix: при наличии `--summary` всегда обновлять хотя бы summary/summary_manual, даже если `manually_reviewed=1`; или изменить skill чтобы при detect `manually_reviewed=1` передавал `--force`.
- **BUG-DUPLICATE-DELETED-MOVED** (подтверждён): task файлы после `Edit` (статус → done) и `Bash mv` попали в artifacts как ОБА — `deleted` (absolute path, от Edit + post-check) и `moved_from`/`moved_to` (relative path, от mv regex). Пример: `SA-T023_bugfix_jsonl-integrity.md` появился и как deleted, и как moved_from в экспорте.
- **BUG-HANDOFF-DIFF-MULTI-SESSION** (подтверждён): synthetic diff `SA-HANDOFF.md` включает изменения предыдущих сессий (SA-T017..T036 marked done) — не только текущей. Происходит т.к. HANDOFF не был закоммичен между сессиями.
- **BUG-UNIQUE-INDEX-SILENT-FAIL** (новый, предположительно): `CREATE UNIQUE INDEX IF NOT EXISTS idx_session_artifacts_unique ON session_artifacts(session_id, file_path)` добавлен в executescript. Если в существующей БД уже есть дубли по (session_id, file_path) — индекс не создаётся, ошибка может быть проглочена executescript. Требует проверки + добавления предварительной дедупликации перед созданием индекса.

**Ручные правки в архиве (verify-archive):**
- SQLite: `summary`/`summary_manual` исправлены на корректный (UPDATE)
- SQLite: `manually_reviewed` сброшен в 0
- SQLite: `session_tags` полностью заменены (убран `bugs-to-task`, добавлены `intro/accept`, `domain:backend`)
- SQLite: `session_tasks` заменены: SA-T030/T031 → SA-T023/T024/T025/T027/T028
- SQLite: `session_artifacts` заменены на корректные для этой сессии
- Export .md: summary исправлен через `sed`

---

## Сессия 2026-04-03_12_SessionArchive_claude_7a6c847e — /bugs-to-task (SA-T032..T036) + verify

**Сессия:** `7a6c847e-...` (bugs-to-task: создание SA-T032..T036 из BUGS.md)
**Проверено:** 2026-04-03 (verify-archive — в следующей сессии, после context window compaction)
**Контекст:** /bugs-to-task → создание SA-T032..T036 → /archive-session → /verify-archive (продолжение в следующем контексте).

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-ARTIFACT-EPHEMERAL-CROSS-SESSION (новый) | SA-T032..T036 task-файлы созданы Write в этой сессии, потом moved в Done/ в следующей. При архивации: post-check видит файлы как deleted → ephemeral filter удаляет их. В экспорте остались только BUGS.md и SA-HANDOFF.md | ✅ вручную |
| BUG-HANDOFF-READ-OVERWRITE (новый) | SA-HANDOFF.md был и прочитан (Read) и изменён (Edit) в одной сессии. Modify overwrite-ает read-сигнал в session_artifacts — `detect_events` не видит `action=read` → `handoff_read` event не создаётся | ✅ вручную |

**Исправлено вручную (SQLite + MD):**
- `sessions.summary`/`summary_manual`: исправлен (был "Выполнены SA-T036..." из другой сессии — подхвачен через BUG-EXPORT-DB-DESYNC)
- `session_artifacts`: добавлены SA-T032..T036 (created)
- `session_tasks`: добавлен actions=created для SA-T032..T036
- `session_events`: добавлен `handoff_read`
- Export MD: добавлены artifacts SA-T032..T036, event handoff_read

**Новые баги:**

- **BUG-ARTIFACT-EPHEMERAL-CROSS-SESSION:** Файлы, созданные Write в сессии A, затем перемещённые mv в сессии B — при архивации сессии A постфактум попадают в ephemeral filter (created+deleted в одной сессии) и исчезают. Root cause: post-check видит файл absent, помечает deleted, ephemeral filter убирает его. Fix: не применять ephemeral filter для файлов где delete произошёл в другой сессии (нужен timestamp или sessionId boundary).

- **BUG-HANDOFF-READ-OVERWRITE:** Read HANDOFF.md + Edit HANDOFF.md в одной сессии → в session_artifacts остаётся только `modified`, read-сигнал потерян → `handoff_read` event не детектируется. Root cause: при update artifact в extract_artifacts новый action overwrite-ает старый. Fix: при `action=modified` на файл с существующим `read` — добавлять отдельный artifact-row или сохранять read-флаг.

- **BUG-EXPORT-DB-DESYNC:** `cmd_archive_current` вызывал `export_markdown(sid, messages, metadata)` даже когда `write_session` вернул early-exit из-за `manually_reviewed=1`. Экспорт записывался с данными нового запуска (summary, tags и т.д.) вместо данных из DB. Fix: реализован в SA-T036-followup — `write_session` теперь возвращает `(sid, skipped)`, `cmd_archive_current` пропускает `export_markdown` при `skipped=True`.

---

## Сессия 2026-04-03_12-SessionArchive_claude_959f6556 — /bugs-to-task + archive + verify

**Сессия:** `959f6556-f664-42db-bdfc-b314a6a48e81`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /bugs-to-task → создание SA-T032..T036 (5 задач из BUGS.md) → /archive-session → /verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-ARTIFACTS-WRONG-SESSION (повторяется) | Artifacts содержали SA-T021/T026/T030 (deleted), session_archive.py (modified), SA-CHANGELOG.md (modified) — из предыдущей сессии. Реальные: BUGS.md, SA-T032..T036 — отсутствовали | ✅ вручную |
| BUG-TASKS-FROM-PREV-SESSION (новый) | Tasks: SA-T021, SA-T026, SA-T030 — задачи из предыдущей сессии (их файлы были изменены там, остались uncommitted). Текущая сессия работала только с SA-T032..T036 | ✅ вручную |
| BUG-TAGS-WRONG-SKILL (повторяется) | skill:accept, skill:intro — ни тот ни другой не запускался. Подхвачены из HANDOFF-контекста или command-message без temporal filter | ✅ вручную |
| BUG-DOMAIN-BACKEND-FALSE (повторяется) | domain:backend — в сессии не было backend-кода, только docs/task-файлы | ✅ вручную |

**Исправлено вручную (SQLite + MD):**
- `session_tasks`: удалены SA-T021/T026/T030; добавлены SA-T032..T036 (created)
- `session_tags`: удалены domain:backend, skill:accept, skill:intro; добавлены skill:bugs-to-task, skill:archive-session, skill:verify-archive
- `session_events`: добавлен `task_docs_updated`
- `session_artifacts`: удалены 12 чужих (SA-T021/T026/T030 deleted/moved, session_archive.py, SA-CHANGELOG.md, README.md); добавлены BUGS.md (modified) и SA-T032..T036 (created)
- Export MD: полностью пересобраны секции Tags/Tasks/Events/Artifacts/Diffs

**Новые наблюдения:**
- **BUG-TASKS-FROM-PREV-SESSION:** task extractor захватывает задачи из предыдущей сессии через uncommitted file changes (те же что BUG-ARTIFACTS-WRONG-SESSION). SA-T030.md изменился в предыдущей сессии, остался uncommitted → попал в tasks текущей. Fix: тот же что SA-T034 — temporal boundary.
- **BUG-TAGS-WRONG-SKILL (уточнение):** `intro`/`accept` в skill-тегах без Skill tool call — вероятно из HANDOFF upfront или из command-message в JSONL без temporal filter. Root cause аналогичен SA-T034.

---

## Сессия 2026-04-03_12_SessionArchive_claude_2a640d04 — /bugs-to-task + archive + verify

**Сессия:** `2a640d04-23f0-423c-b972-c685fa4969fb`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Запуск /bugs-to-task: анализ BUGS.md за 2026-04-03/04-02, создание SA-T030 и SA-T031, обновление tracking table и SA-HANDOFF.md.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-JSONL-CROSS-SESSION-REGRESSION (новый) | Tasks: SA-T023/T024/T025/T027/T028 из предыдущей сессии — SA-T034 помечен ✅fixed, но баг воспроизвёлся. Artifacts: README.md, session_archive.py, SA-CHANGELOG.md, SA-T023..T028 deleted/moved — все из предыдущей сессии в том же JSONL-файле | ✅ вручную |
| BUG-SKILL-PHANTOM | skill: accept и skill: intro — ложные, не использовались в сессии | ✅ вручную |

**Исправлено вручную (SQLite + MD):**
- `session_tasks`: заменены SA-T023..T028 → SA-T030 (created), SA-T031 (created)
- `session_tags`: удалены skill: accept, intro, domain: backend; добавлен skill: bugs-to-task
- `session_artifacts`: заменены 19 записей из предыдущей сессии → 8 реальных (BUGS.md modified, SA-HANDOFF.md modified, SA-T030/T031 created, SA-T021/T029/T026/T023 read)
- `## Diffs`: убраны все диффы из предыдущей сессии (SA-T023..T028 edit_snippets, session_archive.py); заменены на session-local патчи SA-HANDOFF.md, BUGS.md, SA-T030/T031 created

**Новые наблюдения:**
- **BUG-JSONL-CROSS-SESSION-REGRESSION:** SA-T034 и SA-T017 помечены ✅fixed, но archive-current по-прежнему захватывает артефакты из предыдущей сессии в том же JSONL-файле. Один JSONL накапливает несколько сессий (разные session_id). Timestamp-фильтрация (SA-T034) не работает или не включена для всех путей. Root cause: JSONL содержит tool calls и сообщения от предыдущих сессий без чёткого session boundary. Рекомендация: при archive-current фильтровать tool calls по `session_id` из метаданных JSONL, а не только по timestamp.
- **BUG-SKILL-PHANTOM (recurring):** `accept` и `intro` появились как skill-теги, хотя в этой сессии эти скиллы не вызывались. Вероятно, скрипт нашёл их в `<command-message>` тегах из transcript предыдущей сессии в том же JSONL.

---

## Сессия 2026-04-03_12-SessionArchive_claude_191533b7 — SA-T017 + SA-T033 impl + verify

**Сессия:** `191533b7-649e-4dee-9ee5-808d684608cf`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /intro + реализация SA-T017 (archive boundary) и SA-T033 (shell-read trace) + /accept.

**Найденные проблемы:**
- **BUG-MV-QUOTED-PATHS-WITH-SPACES** (подтверждён): `mv "docs/3. tasks/SA-T017..." "docs/3. tasks/Done/..."` — mv-парсер (`\S+`) разбил путь по пробелу → в artifacts попало `/Users/.../docs/3.` (moved_from) и `tasks/SA-T017...` (moved_to). Реальные файлы (SA-T017, SA-T033 task docs) показаны как `deleted` вместо `moved_from`.
- **BUG-HANDOFF-DIFF-MULTI-SESSION** (подтверждён): synthetic diff SA-HANDOFF.md включает изменения предыдущих сессий (SA-T018/T029/T031/T035 marked done) — не только наши. Происходит когда HANDOFF модифицируется между Read tool и концом сессии другими процессами.

**Ручные правки в архиве (verify-archive):**
- SQLite: удалены 3 broken artifacts (`docs/3.`, `tasks/SA-T017...`, `tasks/SA-T033...`)
- SQLite: SA-T017/SA-T033 task file action исправлено `deleted` → `moved_from`
- SQLite: добавлены корректные `moved_to` записи для Done/ путей
- export .md: обновлена секция `## Artifacts` аналогично

---

## Сессия 2026-04-03_12-SessionArchive_claude_6f055acb — verify-archive context window fix + sqlite timeout

**Сессия:** `6f055acb-9caa-4737-b112-33e59e016e12`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Обсуждение архитектуры archive+verify, fix verify-archive.md, sqlite3.connect timeout=30.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-RERUN-OVERWRITE-DURING-VERIFY (новый) | При запуске verify-archive скрипт запустился повторно (видимо через hook или overwrite guard не сработал) и перезаписал export .md, уничтожив ручные правки артефактов | ✅ вручную (восстановлены) |
| BUG-SUMMARY-WRONG-SESSION-ON-RERUN (новый) | При повторном запуске summary подставился от **другой** сессии ("Реализованы SA-T018, SA-T031, SA-T035...") — полностью не та сессия. Overwrite guard не поймал | ✅ вручную (исправлен) |
| BUG-ARTIFACTS-OUTSIDE-CWD-MISSING (новый) | Файлы изменённые/прочитанные за пределами CWD проекта (`~/.claude/commands/verify-archive.md`, `archive-session.md`) не попадают в Artifacts. Парсер фильтрует только по CWD | ✅ вручную (добавлены) |

---

## Сессия 2026-04-03_12-SessionArchive_claude_cc8571e3 — SA-T029 EvidenceAccumulator + accept + archive + verify

**Сессия:** `cc8571e3-c66f-40c1-afbf-f151117a7903`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /next → SA-T029 (EvidenceAccumulator архитектура, derive_domain_tags, BUG-TAGS-DOMAIN-DATABASE-FALSE) → /accept → /archive-session → /verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-EVENTS-LITERAL-STRINGS (новый) | `commit_made` и `tests_run` в Events — не запускалось ни `git commit`, ни `pytest`. Источник: тестовый `python3 -c "...{'command': 'pytest tests/'}...{'command': 'git commit -m test'}..."` — строковые литералы внутри python3 -c команды были распознаны `_detect_command_events` как реальные команды | ✅ вручную (удалены из Events) |
| BUG-MV-QUOTED-PATHS-WITH-SPACES (новый) | Artifacts содержали мусорные записи `/docs/3.` (moved_from) и `tasks/SA-T029_...md` (moved_to) вместо правильного пути `docs/3. tasks/Done/SA-T029_...`. Причина: `mv` regex `\S+` рвёт пути по пробелу, даже если путь в кавычках | ✅ вручную (удалены мусорные артефакты) |

**Исправлено вручную (SQLite + MD):**
- `session_events`: удалены `commit_made`, `tests_run`
- `session_artifacts`: удалены `/docs/3.` (moved_from) и `tasks/SA-T029_...md` (moved_to)
- Export MD: соответствующие секции обновлены

**Новые баги:**

### BUG-EVENTS-LITERAL-STRINGS
**Root cause:** `_detect_command_events(cmd)` применяет regex к ВСЕЙ строке Bash-команды. Когда Claude запускает `python3 -c "..."` с кодом внутри, строковые литералы Python (`'pytest tests/'`, `'git commit -m test'`) подходят под regex-паттерны событий.
**Воспроизведение:** Запустить `python3 -c "cmd = 'pytest tests/'; print(cmd)"` — создаст ложный `tests_run`.
**Рекомендуемый фикс:** В `_detect_command_events`, перед матчингом извлекать только "верхний уровень" команды (первый токен + flags), игнорируя содержимое кавычек. Или ограничить матчинг: только если команда НАЧИНАЕТСЯ с паттерна (`re.match` вместо `re.search`), либо перед строковыми литералами (до первой открывающей `"`/`'`).

### BUG-MV-QUOTED-PATHS-WITH-SPACES
**Root cause:** Regex `r'\bmv\s+(\S+)\s+(\S+)'` использует `\S+` (non-whitespace), что не обрабатывает пути в кавычках с пробелами. Путь `"docs/3. tasks/file.md"` разрезается на `"docs/3.` и `tasks/file.md"`.
**Воспроизведение:** `mv "path/with spaces/file.md" "dest/with spaces/file.md"` — src и dst будут некорректными.
**Рекомендуемый фикс:** Использовать `shlex.split(cmd)` для разбора команды вместо regex, либо расширить regex для захвата кавычек: `r'\bmv\s+("(?:[^"]+)"|\'(?:[^\']+)\'|\S+)\s+("(?:[^"]+)"|\'(?:[^\']+)\'|\S+)'` с последующей strip-кавычек.

---

## Сессия 2026-04-03_cleaning-bot_claude_09796f55 — T288 fix + deploy + accept + archive + verify

**Сессия:** `09796f55-a596-4051-a610-0a57b851165c`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** T288 (S41 Phase 3, tma_homestager): /intro + выполнение T288 (Skip/Skip zone fix, диагностика модалки) + deploy + Trello move + /accept + /archive-session + /verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-ARTIFACTS-WRONG (новый вариант) | Единственный артефакт — `/Users/is/.claude/settings.json` (не менялся). Реальные изменённые файлы (VideoRecordingSimple.tsx, ZoneSelection.tsx, CHANGELOG.md, HANDOFF.md, spec) — отсутствовали | ✅ вручную |

**Исправлено вручную (SQLite + MD):**
- `sessions.ai_model` → `claude-sonnet-4-6`
- `session_tags`: `model` → `claude-sonnet-4-6`; удалены `domain:backend/database/tests/architecture/autodev`; удалены мусорные skills (20+ тегов); оставлены `domain:frontend/docs`, добавлены `skill:code/trello/deploy`
- `session_tasks`: добавлен T288 с action `fix,debug`
- `session_events`: удалены `tests_run`, `pr_created`; добавлен `build_run`
- `session_artifacts`: удалён `/Users/is/.claude/settings.json`; добавлены 6 реально изменённых файлов
- Export MD: все секции пересобраны; Diffs заменены реальными git diff из коммитов c137180 и 290739f

**Новые баги:**
- **BUG-PROJECT-SLUG-MISMATCH (новый):** `PROJECT_SLUG` вычисляется без leading dash (`Users-is-Cleaning-bot`), а реальная Claude-директория содержит leading dash (`-Users-is-Cleaning-bot`). Это баг в формуле `sed s|^/||`. Нужно либо `PROJECT_SLUG=$(echo "$PWD" | sed 's|^/|-|; s|/|-|g')`, либо `$(echo "$PWD" | tr "/" "-")`. Workaround: явно искать в директории с dash.
- **BUG-ARTIFACTS-WRONG:** Скрипт детектирует settings.json как артефакт сессии, хотя он не менялся. Видимо, скрипт смотрит на все Read/Write tool calls в JSONL, включая чтение settings.json через системные операции. Нужен фильтр: только файлы внутри `cwd`.

---



## Сессия 2026-04-03_Arbitra_claude_7d053534 — codereview T02 Round 2 + fixes N1/N2 + accept

**Сессия:** `7d053534-e969-4d94-a1e0-9ed203857191`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Code Review Round 2 по T02 (авторизация демо-бота Алевтина): найдено 2 MEDIUM (N1 — неполная регистрация middleware CallbackQuery, N2 — KeyError в update_context). Оба фикса применены. T02 заакцептирован, CHANGELOG обновлён.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-EVENT-PHANTOM | `changelog_read` в Events — CHANGELOG не читался через Read tool в этой сессии, только писался | ✅ вручную (удалён) |

**Исправлено вручную:**
- `sessions.ai_model` → `claude-sonnet-4-6`
- `session_tags`: полный пересброс — удалены фантомы (`frontend`, `tests`, `autodev`, `architecture`, `command-message`, `command-name`, `dev`, `ide`, `subagents`, `visualcheck`); оставлены реальные (`backend`, `docs`, `review`, `intro`, `codereview`, `fix`, `accept`, `archive-session`); исправлен `model`-тег
- `session_tasks`: T01/T04/T07/T09 удалены, оставлен T02 с action `reviewed,fixed,accepted`
- Export MD: `| Model | claude |` → `claude-sonnet-4-6`; Tags/Tasks пересобраны; Diffs заменены минимальными без пустых строк; `changelog_read` убран из Events

**Новые наблюдения:**
- **BUG-TAGS-XML-MARKERS:** Теггер захватывает содержимое XML-тегов `<command-message>`, `<command-name>` из тела диалога как skill-теги. Нужна фильтрация: теги skill должны выводиться только из фактических вызовов Skill-тула, а не из текста сообщений.
- **BUG-EVENT-PHANTOM:** Events генерируются без привязки к реальным tool-calls. `changelog_read` появился хотя Read-вызова на CHANGELOG не было — только Edit/Write. Рекомендация: Events должны верифицироваться по artifact-списку (если файл только в `modified`, не в `read` — `*_read` event не добавлять).

## Сессия 2026-04-03_sproektirui_codex_019d52e2 — codereview T145 + session-archive

**Сессия:** `019d52e2-f9c7-74f0-9532-5e3f1cd91f89`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Codex-сессия по `sproektirui`: выполнен `codereview` задачи `T145` с чтением task-файла, backend import/sync/calc path и реального Teplofort xlsx; в `T145` добавлена секция `Code Review — 2026-04-03 13:33` с двумя `HIGH` finding'ами, после чего выполнен `session-archive`.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-ARTIFACT (повторяется) | `Artifacts` содержали только modified task-файл и два мусорных pseudo-artifact `event:tests`; пропали реально прочитанные `.codex/codereview-local.md`, Teplofort xlsx и backend-файлы review-scope | ✅ вручную |

**Исправлено вручную:**
- `sessions.summary` и export `## Summary` переписаны под фактический `codereview T145`, без ссылок на context-only `T097`/`T123`
- `session_tasks` очищен до `T145`
- `session_tags` пересобран до реальных тегов: `backend`, `database`, `docs`, `review`, `tests`; skills: `codereview`, `session-archive`
- `session_events` пересобран до подтверждённых `tests_run`, `task_docs_updated`, `session_archived`
- `session_artifacts` очищен от `event:tests` и дополнен реально прочитанными config/xlsx/backend-файлами review-scope
- diff для `T145...md` заменён на `manual_session_local`: только добавленный в этой сессии блок `Code Review — 2026-04-03 13:33`, без захвата pre-existing `13:31`
- `session_messages` дедупнуты по соседним идентичным блокам; `sessions.msg_count` исправлён `33 -> 21`, `user_msg_count` пересчитан `6 -> 4`
- export `2026-04-03_sproektirui_codex_019d52e2.md` перегенерирован из исправленной SQLite-записи

**Новые наблюдения:**
- Diff extractor всё ещё не умеет отделять session-local patch от pre-existing dirty-worktree изменений в уже изменённом task/doc файле, если fallback идёт через `git_base`
- Artifact extractor не должен сохранять `event:*` pseudo-paths в `session_artifacts`; это event-evidence, а не файловые артефакты
- Message/transcript extractor по-прежнему пишет соседние дубли `(role, text)` и только потом считает `Messages`; нормализация должна происходить до сохранения в SQLite и до markdown-export

## Сессия 2026-04-03_sproektirui_codex_019d51d4 — intro + review T145/T146 + session-archive

**Сессия:** `019d51d4-b2cd-71f1-8ad5-19388d6372a8`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Codex-сессия по `sproektirui`: выполнен `intro`, затем придирчивое ревью draft-задач `T145` и `T146` against Trello comments, screenshots и текущий code path; в оба task-файла добавлены секции `Code Review`, после чего выполнен `session-archive`.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-ARTIFACT-INCOMPLETE (повторяется) | В `Artifacts` остались только 2 modified task-файла; пропали реально прочитанные `HANDOFF`, `ARCHITECTURE`, `S14` spec, code-файлы, skill docs и просмотренные Trello screenshots | ✅ вручную |

**Исправлено вручную:**
- `sessions.summary` переписан под фактическую review-сессию по `T145`/`T146`.
- `session_tags` очищен и пересобран до реальных тегов: `frontend`, `backend`, `database`, `docs`, `review`; skills: `intro`, `codereview`, `session-archive`.
- `session_events` пересобран до подтверждённых `handoff_read`, `architecture_read`, `spec_read`, `task_docs_updated`, `session_archived`.
- `session_tasks` очищен до `T145` и `T146`.
- `session_artifacts` заново собран по pre-archive tool evidence; для `T145` и `T146` подставлены реальные unified diff из before-snapshot + `apply_patch`, без пустых строк и без synthetic full-file scope.
- Export `2026-04-03_sproektirui_codex_019d51d4.md` перегенерирован из исправленной SQLite-записи.

**Новые наблюдения:**
- Если файл уже существовал вне git и был изменён через `apply_patch`, архив не должен строить diff как `"" -> current file`; нужно приоритетно использовать before-snapshot из read tool output или raw JSONL текущей сессии.
- Парсер задач и тегов сейчас слишком доверяет prose и skill-mentions. Нужна более жёсткая привязка к фактическим tool calls: task должен появляться только если был рабочим объектом с изменением/ревью, а skill-tag только если навык реально выполнялся до `archive-current`.

## Сессия 2026-04-03_Arbitra_claude_aa723310 — codereview T02_s01_auth + fix R1–R5 + verify-archive

**Сессия:** `aa723310-d72e-4129-8fbe-2c5f27ac3c5b`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Код-ревью T02_s01_auth (авторизация демо-бота Алевтина): 2 HIGH + 3 MEDIUM + 2 LOW. Применены фиксы R1–R5. Обнаружен дополнительный NameError (PHONE_USE_BUTTON не импортирован) — исправлен при verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-MISSING-IMPORT-IN-FIX (новый, в коде) | При применении fix R4 (contact.py: проверка владельца контакта) — добавлено использование `PHONE_USE_BUTTON` без добавления его в import-строку. NameError при runtime. Обнаружен при verify-archive через проверку контента synthetic diff | ✅ исправлен в contact.py |

**Исправлено вручную:**
- `sessions.ai_model` → `claude-sonnet-4-6`
- `sessions.summary` → актуальный summary T02 (перезаписан из-за BUG-ARCHIVE-OVERWRITE)
- `session_tags`: полный пересброс (DELETE+reinsert) — удалены фантомы, добавлены реальные `intro`, `codereview`, `fix`, `archive-session`; `model` → `claude-sonnet-4-6`
- `session_tasks`: T01/T04/T07 удалены, оставлен T02 `reviewed,fixed`
- Export MD: полностью перезаписан с чистыми диффами без пустых строк
- `demo_bot/handlers/contact.py`: добавлен `PHONE_USE_BUTTON` в import

**Новые наблюдения:**
- **BUG-ARCHIVE-OVERWRITE:** Если `archive-current` вызывается дважды на одном JSONL (или JSONL продолжает расти, и кто-то ещё запускает архивацию), второй вызов перезаписывает summary и msg_count. Явно переданный `--summary` при первом вызове теряется. Рекомендация: при повторном `archive-current` с тем же session_id — обновлять только msg_count и tool_call_count, НЕ перезаписывать summary если он уже был задан вручную (добавить флаг `--keep-summary`).
- **BUG-SQLITE-NO-UNIQUE-CONSTRAINT:** Добавить UNIQUE constraint `(session_id, category, value)` в `session_tags` и `(session_id, task_id)` в `session_tasks`. Это позволит использовать `INSERT OR IGNORE` без риска дублей.
- **BUG-MISSING-IMPORT-IN-FIX:** При code fix следует автоматически проверять, что все использованные идентификаторы присутствуют в import-строках файла. Можно добавить статический анализ (grep на `NameError`-риск) как часть verify-фазы fix-скилла.

## Сессия 2026-04-03_sproektirui_codex_019d51c7 — intro + rewrite T145/T146 + session-archive

**Сессия:** `019d51c7-7954-7d42-a188-f4cf7c292f0c`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Codex-сессия по `sproektirui`: выполнен `intro`, затем по находкам из review переписаны draft-задачи `T145` и `T146`, удалены их review-секции, после чего выполнен `session-archive`.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-ARTIFACT (повторяется) | `Artifacts` содержали только 2 task-файла и не включали реально прочитанные `HANDOFF`, `ARCHITECTURE`, `codereview-local`, code-файлы и skill docs | ✅ вручную |

**Исправлено вручную:**
- `sessions.summary` и export `## Summary` переписаны под фактический outcome rewrite-сессии по `T145`/`T146`
- `session_tasks` очищен до `T145`, `T146` с action `reviewed,updated`
- `session_tags` пересобран до реальных тегов: `backend`, `database`, `docs`, `frontend`, `review`; skills: `fix`, `intro`, `session-archive`
- `session_events` пересобран до подтверждённых `handoff_read`, `architecture_read`, `task_docs_updated`, `session_archived`
- `session_artifacts` дополнен реально прочитанными файлами; оба task-файла переведены из `deleted` в `modified`
- diff для `T145...md` и `T146...md` пересобран по before-snapshot из raw JSONL `sed`-выводов; `diff_source` заменён на `session_snapshot`
- `session_messages` дедупнуты по соседним идентичным блокам; `sessions.msg_count` исправлён `27 -> 17`, `user_msg_count` пересчитан `-> 5`
- export `.md` синхронизирован с исправленной SQLite-записью

**Новые наблюдения:**
- **BUG-ARTIFACT-WRONG-OP (уточнение):** если один `apply_patch` в рамках одной сессии делает `Delete File` + `Add File` для одного и того же пути, архив сейчас слепо пишет одновременно `A path` и `D path` из tool-output и классифицирует surviving файл как `deleted`. Нужно схлопывать `A+D` по одному пути в `modified`, если путь существует после команды.
- **BUG-DIFF-UNTRACKED-SCOPE (подтверждение):** для untracked dirty-worktree task-файлов архив снова строит synthetic diff как `"" -> current file`, хотя raw JSONL уже содержит пригодный before-snapshot из `sed`/`cat` read-вызовов. Рекомендация: при наличии предыдущего read того же пути в текущей сессии строить diff от него, а не от пустого файла.
- **BUG-SKILL-PHANTOM (уточнение):** `verify-archive` не должен попадать в skill-tags, если он был только запрошен после `session-archive` и ещё не выполнялся на момент архивации. При этом сам `SKILL.md` может и должен оставаться в `Artifacts` как реально прочитанный файл.

## Сессия 2026-04-02_sproektirui_claude_eb2f67de — code review T142 + accept

**Сессия:** `eb2f67de-8944-4a8a-a9e8-d7e5283bdbdd`
**Проверено:** 2026-04-02 (verify-archive)
**Контекст:** Код-ревью T142 (скрытие legacy CRUD «Аналоги серий»): 2 находки в тестах. Деплой, акцепт T142, Trello в «Ревью/вопросы».

| BUG | Симптом в этой сессии |
|-----|----------------------|
| BUG-DIFF-MISSING | Diff commit `review(T142)` (добавление code review секции) отсутствовал |
| BUG-ARTIFACT | `RecordForm.jsx` пропущен из artifacts (был grep) |

**Исправлено вручную:**
- `ai_model` → `claude-sonnet-4-6` (sessions + session_tags + MD)
- Tags: убраны `domain:database/architecture/autodev`, `skill:dev/ide/localhost/subagents`; добавлены `skill:codereview-local/accept/archive-session`
- Tasks: удалён T143
- Events: добавлен `session_archived`
- Artifacts: добавлен `RecordForm.jsx (read)`
- Diffs: `a//` → `a/`; hunk headers расширены; добавлен diff для review-коммита

**Новые наблюдения:**
- **BUG-DIFF-SPLIT:** файл правился дважды (review-commit + accept-commit) — diff показывает только git_head последнего. Первый edit_snippet теряется. Рекомендация: для файла с N правками в сессии — объединять или показывать оба с пометкой commit-sha.
- **BUG-JSONL-MTIME:** `ls -t | head -1` вернул `d3cec0d7` (4 msg) вместо `eb2f67de` (27 msg) — mtime не всегда синхронен. Рекомендация: среди топ-2 по mtime брать файл с большим числом строк.

---

## Сессия 2026-04-02_sproektirui_claude_d3cec0d7 — intro + T144 создание + archive

**Сессия:** `d3cec0d7-354e-43b1-aabf-bb68c6a15b68`
**Проверено:** 2026-04-02 (verify-archive)
**Контекст:** Claude-сессия по sproektirui: `/intro`, поиск Trello-карточки в «На доработку», расследование root cause кэш-бага (три слоя), создание задачи T144, обновление HANDOFF.md, спеки S14, карточки Trello, затем `archive-session` и `verify-archive`.

| BUG | Симптом в этой сессии |
|-----|----------------------|
| BUG-REPEAT | `ai_model` снова записан как `claude` вместо `claude-sonnet-4-6` — проблема не исправлена с прошлой сессии |

**Исправлено вручную:**
- `sessions.ai_model` и `session_tags model` исправлены на `claude-sonnet-4-6` в SQLite
- `session_tags`: удалены `domain:database/tests/ci_cd/autodev/review`, `skill:command-message/command-name/dev/ide`; добавлены `domain:trello`, `skill:archive-session/verify-archive`
- `session_tasks`: удалены T139–T142; оставлены T143 (read), T144 (created)
- `session_events`: удалены `review_done`, `task_completed`; добавлены `task_created`, `trello_updated`
- Export .md: синхронизирован с SQLite по всем полям
- Synthetic diff T144: убраны 76 пустых строк (Python-скрипт, collapse blank lines between `+`-lines)

**Корневая причина BUG-NEW-D (synthetic diff):**
- При генерации synthetic diff для нового файла скрипт добавляет пустую строку после каждой строки содержимого. Вероятно, `\n` в строке контента + `\n` как разделитель строк в diff-рендере дают двойной перенос.
- Источник: функция генерации synthetic diff в `session_archive.py`, ищи место где строки файла объединяются в diff-блок.

**Рекомендации по фиксу BUG-NEW-D:**
- В генераторе synthetic diff: использовать `content.splitlines()` и join через `\n+`, а не `\n\n+`, либо strip trailing `\n` с каждой строки перед добавлением в diff-блок.
- Или: читать файл построчно и сразу добавлять `+` без дополнительного `\n` между строками.

---

## Сессия 2026-04-02_sales_claude_68276310 — CV EN для Ingingo OS (React/Firebase)

**Сессия:** `68276310-98dd-4bcd-abf5-003fb02e5138`
**Проверено:** 2026-04-02 (verify-archive)
**Контекст:** Создание английской версии CV Серебренникова под вакансию React/Firebase-разработчика в Ingingo OS. Прочитали PDF CV, исследовали проекты (sproektirui, cleaning-bot, bizdevim, extractime, sternmeister) через Explore-субагент, создали HTML + сгенерировали PDF через Chrome headless.

| BUG | Симптом в этой сессии |
|-----|----------------------|
| BUG-ARTIFACT | PDF `CV_Serebrennikov_EN_React_2026.pdf` (created via Chrome headless) пропущен из artifacts |

**Исправлено вручную:**
- `sessions.ai_model` → `claude-sonnet-4-6` (SQLite)
- `session_tags`: удалены `model:claude`, `assistant:claude` → заменены на `claude-sonnet-4-6`; удалены `domain:database/autodev`, `skill:command-message/command-name/dev/ide`; добавлены `domain:ai`, `skill:archive-session`
- Export .md: синхронизирован (Model, Tags, Artifacts)
- Diff format: не правили — слишком большой объём HTML (~350 строк × 2)

**Новое наблюдение — BUG-XML-TAGS (уточнение BUG-33):**
- Парсер считывает `<command-message>` и `<command-name>` из тела user-сообщений как skill-теги.
- Рекомендация: skills извлекать только из tool_use блоков с именем `Skill`, а не из произвольного текста пользователя.

---

## Сессия 2026-04-02_sproektirui_codex_019d4d8b — fix T144 + archive + verify

**Сессия:** `019d4d8b-64ee-7a33-ba92-f2a8ff2adc49`
**Проверено:** 2026-04-02 (verify-archive)
**Контекст:** Codex-сессия по sproektirui: fix задачи T144 из founder review, правка frontend-кэша каталога, обновление review-статусов в task doc, локальная верификация (`eslint` + `vite build` через `node v20.20.1`), ответ на вопрос про stage deploy, затем `session-archive` и ручная проверка записи через `verify-archive`.

| BUG | Симптом в этой сессии |
|-----|----------------------|
| BUG-ARTIFACT | `Artifacts` недособрали session-local reads: в записи были только 3 modified файла, но отсутствовали реально прочитанные `.codex/codereview-local.md`, `CatalogPage.jsx`, `CategorySection.jsx`, `BrandPage.jsx`, backend router, оба `package.json` и skill docs `session-archive` / `verify-archive` |

**Исправлено вручную:**
- `sessions.summary` и export `## Summary` переписаны под фактический outcome fix-сессии по `T144`
- `sessions.open_issues` заменён на реальные unresolved findings T144 (`MEDIUM #4`, `LOW #1`, `LOW #5`)
- `session_tasks` очищен до `T144`
- `session_tags` пересобран до реальных тегов: `frontend`, `docs`, `review`, `shell`; skills: `fix`, `session-archive`, `verify-archive`
- `session_events` пересобран до подтверждённых `docs_updated`, `session_archived`
- `session_artifacts` дополнен реально прочитанными shell-read файлами и skill docs; ложные omissions устранены
- diff для `T144...md` пересобран как session-local unified diff от before-snapshot из archive artifact content; `diff_source` заменён на `session_snapshot`
- `session_messages` дедупнуты по соседним идентичным блокам; `sessions.msg_count` исправлён `41 -> 23`, `user_msg_count` пересчитан `-> 5`
- export `.md` синхронизирован с исправленной SQLite-записью

**Корневая причина:**
- summary/open-issues/tasks extraction всё ещё читает весь transcript и ловит skill-body примеры, context-only ids и in-progress commentary вместо explicit user goal + final outcome
- tag/event extraction всё ещё выводит domain/skill/events из слов в prose, а не из подтверждённых tool calls и реальных file touches
- artifact extraction по-прежнему недобирает shell-read evidence и склоняется к “только modified files”
- diff extraction для dirty-worktree doc/task files всё ещё не держит session-local before-snapshot и fallback'ит в misleading synthetic full-file add
- transcript/message extraction по-прежнему пишет часть user/assistant blocks дважды

**Рекомендации по фиксу:**
- Для `Summary`, `Open Issues` и `Tasks` приоритизировать explicit user goal + реально изменённые task/code files + финальный assistant outcome; полностью исключить skill-definition text и промежуточные progress-updates
- Для `Tags` и `Events` разрешать только значения, подтверждённые tool-call evidence: skill invocation, `archive-current`, `apply_patch`/edit по doc-файлам, test/build commands и т.д.
- Для `Artifacts` собирать полный shell-read trace (`sed`, `rg`, `tail`, `sqlite3`, чтение skill/docs), а не только modified set
- Для dirty/untracked modified doc/task файлов сохранять first-read before-snapshot и строить unified diff строго из `before_text` / `after_text`, без synthetic full-file add
- Перед записью `session_messages` и перед export `## Transcript` дедупить соседние идентичные `(role, text)` блоки; `Messages` считать уже после этой нормализации

---

## Сессия 2026-04-03_sproektirui_claude_eba39d60 — codereview T146 + archive-session + verify-archive

**Сессия:** `eba39d60-8d1e-4e47-b47e-223b1bfdc7c5`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Код-ревью задачи T146 (пагинация радиаторов, top-10 preview). Прочитаны: task-файл T146, ResultTabs.jsx, previewRank.js, previewRank.test.js, ResultTabs.test.jsx, DeviceCalculator.jsx, codereview-local.md. Запущены ESLint и unit-тесты (25/25). Добавлена секция `## Code Review — 2026-04-03 15:00` в T146. Затем `/archive-session` и `/verify-archive`.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-ARTIFACT-WRONG-FILE (новый) | Artifacts содержал T145 file как `modified` и BUGS.md как `read`. Реально в этой сессии был изменён T146 и прочитаны JS-файлы review-scope. | ✅ вручную (пересобраны артефакты) |

**Исправлено вручную:**
- `sessions.ai_model` → `claude-sonnet-4-6`
- `session_tags`: model/assistant → `claude-sonnet-4-6`; удалены `domain:autodev/backend/ci_cd/database`, `skill:command-message/command-name/dev/ide/localhost/subagents/visualcheck`; добавлены `skill:archive-session`, `skill:verify-archive`
- `session_tasks`: удалены T042/T099/T145; добавлен T146 (reviewed)
- `session_events`: удалены `handoff_read/changelog_read/deploy/task_completed`; добавлен `session_archived`
- Export MD: Model → claude-sonnet-4-6; Tags/Tasks/Events/Artifacts пересобраны; Diffs заменены на корректный manual_session_local diff T146 (+48 строк Code Review)

**Новые наблюдения:**

- **BUG-DIFF-WRONG-FILE (новый):** `git_head` diff захватывает ВСЕ uncommitted changes в worktree, включая pre-existing изменения из предыдущих сессий. Если файл X был изменён раньше и остался uncommitted, а текущая сессия трогала только файл Y (untracked `??`), diff покажет X и проигнорирует Y. **Рекомендация:** diff должен строиться только по артефактам с confirmed tool-calls (Write/Edit на конкретный путь), не из `git diff HEAD`.

- **BUG-DIFF-UNTRACKED-SKIP (новый):** Untracked файлы (`??` в git status) полностью пропускаются `git diff HEAD`. В этой сессии T146 был `??`, поэтому diff не содержал никаких изменений к реально изменённому файлу. **Рекомендация:** если артефакт помечен как `modified` но `git diff HEAD` на нём пустой — проверить `git diff --no-index /dev/null <file>` или использовать tool-call history для восстановления diff.

- **BUG-34 (16-й раз подряд):** Воспроизводится в каждой claude-сессии. Парсить `model` из JSONL assistant-сообщений (`usage.model` поле в assistant entries).

---

## BUG-42: Read snapshot содержит cat-n форматирование и system-reminder → synthetic diff показывает замену всего файла

**Обнаружено:** 2026-04-03 (verify-archive, сессия d27a9c09)
**Статус:** ✅ FIXED 2026-04-03 в `session_archive.py`

### Симптом

После реализации BUG-DIFF-UNTRACKED-SCOPE (SA-T002) — использование Read-snapshot как baseline для untracked файлов — synthetic diff для SA-HANDOFF.md и SA-CHANGELOG.md показывал весь файл как замену (`-     1→content` → `+content`).

### Root cause

Claude Code tool_result для Read-инструмента содержит:
1. **cat-n форматированный вывод:** `     1→# Session Archive` вместо `# Session Archive`
2. **`<system-reminder>...</system-reminder>` блоки** — вставляются прямо в тело tool_result

`_build_read_snapshots` хранил эти строки как-есть. При сравнении с реальным содержимым файла unified_diff показывал полную замену всего контента.

### Fix (применён в d27a9c09)

Добавлена функция `_strip_read_tool_formatting(text)`:
- Убирает cat-n префиксы: `re.sub(r"^\s*\d+→", "", text, flags=re.MULTILINE)`
- Убирает system-reminder блоки: `re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.DOTALL)`

Дополнительно: `_build_read_snapshots` пропускает Read с `offset`/`limit` — частичный контент не годится как baseline.

---

## Сессия 2026-04-03_autodev-v2_claude_c7134b7d — codereview #3 ADV-T017 + accept + archive + verify

**Сессия:** `c7134b7d-5378-44b0-a84a-f5371f8ce696`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /intro + codereview #3 ADV-T017 (SQLite state): найдены L_NEW4 (CreateRun/UpdateRun ошибки молча проглатываются) и L_NEW5 (makeRunID second-granularity). /accept T017. /archive-session + /verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-TASK-ACTIONS-INCOMPLETE (новый) | actions=`reviewed` — принят также через /accept, но `accepted` не добавлен | ✅ вручную (→ `reviewed, accepted`) |
| BUG-EVENTS-TASK-COMPLETED-MISSING (новый) | session_events содержит только `session_archived`; при accept T017 → `task_completed` не детектируется | ✅ вручную (INSERT task_completed ADV-T017) |

**Root cause BUG-TASK-ACTIONS-INCOMPLETE:**
`extract_task_ids()` определяет action по типу tool call (Read → reviewed, Edit/Write → modified и т.д.), но `/accept` скилл не генерирует специального маркера. Accept выражается как Edit файлов (статус, HANDOFF, CHANGELOG) — скрипт видит это как `modified`, а не `accepted`. Рекомендация: если задача перемещена в Done/ (файл удалён из текущей папки) и её статус стал `done` — добавлять `accepted` к actions.

**Root cause BUG-EVENTS-TASK-COMPLETED-MISSING:**
`detect_events()` не имеет правила для `task_completed`. Accept выражается через перемещение файла (git mv/bash mv) + Edit статуса. Рекомендация: детектировать `task_completed` когда task-файл перемещён в `Done/` путь в session_artifacts.

**Исправлено вручную (SQLite + MD):**
- session_artifacts: удалены ID 3420 (`docs/3.` moved_from) + 3421 (broken moved_to); добавлена запись с полным путём Done файла (modified)
- session_tasks: T017 → ADV-T017; actions: reviewed → reviewed, accepted
- session_events: добавлен task_completed ADV-T017
- Export MD: Events добавлен task_completed; Tasks исправлены с префиксом и action; Artifacts заменены 2 сломанные строки на 1 корректную
- Export MD Diffs: HANDOFF → edit_snippet (только T017 строка, убраны T016/T020 из предыдущих сессий); T017 task file → edit_snippet (статус + ревью #3 вместо huge deletion diff); S03 spec → edit_snippet (только T017); CHANGELOG → edit_snippet (только T017 запись)

---

## Сессия 2026-04-03_autodev-v2_claude_54332c00 — codereview #4 T020 + /fix (MEDIUM×3) + accept + archive + verify

**Сессия:** `54332c00-1fb8-4678-8670-3ec0d243ca16`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /intro + codereview #4 ADV-T020 (WorktreeManager): 3 MEDIUM + 1 LOW (#14-#17). /fix: amInProgress() helper, SQLite needs_manual_merge статус, WORKTREE_MODE WARNING. /accept T020. /archive-session + /verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-SUMMARY-OVERWRITE-BY-REARCHIVE (новый) | Summary перезаписан с T020-контента на T017-контент. Причина: verify-archive запустил archive-session повторно; второй вызов выбрал тот же JSONL и перезаписал `--summary` ML-сгенерированным вместо нашего ручного. | ✅ вручную (восстановлен T020 summary) |

**Root cause BUG-SUMMARY-OVERWRITE-BY-REARCHIVE (новый):** `verify-archive` скилл вызывает `archive-session` скилл внутри своего flow. Второй вызов `session_archive.py archive-current` без `--summary` заставляет скрипт сгенерировать summary из JSONL содержимого — что перезатирает ручной `--summary` переданный при первом вызове. Рекомендация: `verify-archive` скилл НЕ должен вызывать `archive-session`; он должен только читать и проверять уже созданный экспорт. Если нужно обновить запись — использовать `--update` флаг с явным `--summary`.

**Исправлено вручную (SQLite + MD):**
- sessions: summary восстановлен (T020 content), ai_model → claude-sonnet-4-6
- session_tasks: T017 → T020 (actions: reviewed,fixed,accepted)
- session_tags: assistant → claude-sonnet-4-6; удалены domain database, review; добавлены skill codereview, accept, verify-archive
- session_events: codereview T017 → T020; добавлены linter_run, task_accepted
- session_artifacts: удалены T017/state файлы, phantom SA файлы, event:tests дубли; добавлены worktree.go (modified), run.sh (modified), T020_done.md (modified), CHANGELOG.md (modified), S03 spec (modified), BUGS.md (modified); HANDOFF read → modified
- Export MD: Summary, Tags, Events, Tasks, Artifacts исправлены; Diffs: удалены T017 дифы, добавлены synthetic worktree.go + run.sh + main.go (T020 only)


---

## Сессия 2026-04-03_12_SessionArchive_claude_7f6f1cff — SA-T016/T019/T020/T022 bugfixes + accept + verify

**Сессия:** `7f6f1cff-9256-4557-abc9-74c7b1f46e68`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /intro + реализация SA-T016/T019/T020/T022 (open_issues noise filter, event:* filter, Skill tool detection, cwd filter, A+D collapse, is_error tracking) + /accept + /archive-session + /verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-DUPLICATE-DELETED-MOVED | SA-T016/T019/T020/T022 файлы появились как `(deleted)` (absolute path) + `(moved_from)` (relative) + `(moved_to)` — тройное представление одной mv операции | ✅ вручную (SQLite + MD) |
| BUG-MV-RELATIVE-PATH | `moved_from: ../SA-T016...`, `moved_to: SA-T016..._done.md` — пути относительные к Done/, не нормализованы до project-root relative | ✅ вручную (SQLite + MD) |
| BUG-HANDOFF-DIFF-MULTI-SESSION | Synthetic diff для `SA-HANDOFF.md` показал изменения из 20+ предыдущих сессий (SA-T017..T036) потому что git HEAD старый и всё накопилось без коммита | ⚠️ не исправлено (нет простого фикса без git commit) |

**Root causes:**

**BUG-DUPLICATE-DELETED-MOVED:**
- `extract_artifacts()` post-check (строка ~609): если файл не существует на диске и action∈{modified,created} → меняет на `deleted`. Это срабатывает для файлов прочитанных/отредактированных до mv.
- Одновременно `mv` regex в Bash handler добавляет `moved_from`/`moved_to`.
- Итого: для одного и того же пути в artifacts: `(deleted)` + `(moved_from)` + `(moved_to)`.
- **Fix:** если в artifacts уже есть запись `moved_from` для пути → post-check не должен добавлять `deleted` для этого пути.

**BUG-MV-RELATIVE-PATH:**
- `re.findall(r'\bmv\s+(\S+)\s+(\S+)', cmd)` захватывает сырые аргументы команды.
- Когда mv запускается как `cd .../Done && mv ../foo foo_done.md`, пути захватываются как `../foo` и `foo_done.md`.
- **Fix:** нужно резолвить пути относительно cwd из которого выполнялась Bash команда. Но cwd команды может отличаться от project cwd. Альтернатива: нормализовать `..` пути в `_normalize_artifact_key` через `Path.resolve()` относительно project_root/cwd.

**BUG-HANDOFF-DIFF-MULTI-SESSION:**
- `_synthetic_diff_for_artifact` сравнивает текущий файл с `git show HEAD:<path>`.
- Если HANDOFF.md изменялся в 20 сессиях без git commit между ними, `git show HEAD:...` возвращает очень старую версию.
- `_git_diff_for_artifact` сначала пробует `base_commit..HEAD`, потом `HEAD` — оба возвращают пусто (нет tracked изменений т.к. файл untracked или не закоммичен).
- Fallback на synthetic показывает весь накопленный diff.
- **Fix:** документально ограничить synthetic diff: если перед-snapshot недоступен и файл слишком большой (>SYNTHETIC_DIFF_MAX_LINES) — возвращать `None` вместо full-file diff. Или: требовать git commit в конце каждой сессии (процессный фикс).

**BUG-WRONG-SESSION-ARCHIVE (2026-04-03, сессия 959f6556):**
- `ls -t "$JSONL_DIR"/*.jsonl | head -1` в archive-session skill выбрал `c2a63b7d` (bugs-to-task сессия от 16:34) вместо текущей сессии `959f6556` (SA-T021/T026/T030, от 17:12).
- **Root cause:** на момент выполнения Bash tool call JSONL текущей сессии ещё не записан финально (entries добавляются после завершения tool call). Параллельно запущенные verify-archive агенты могут модифицировать другие JSONL файлы, меняя их mtime. Итог: `ls -t | head -1` возвращает mtime по состоянию ПОСЛЕ tool call, но JSONL текущей сессии оказывается не самым новым.
- **Симптом:** archive сделан для неправильной сессии, summary нашего чата применён к чужому session_id, tasks/artifacts/diffs совпадают с другой сессией.
- **Повторялось:** 1+ раз (2026-04-03).
- **Fix:** В archive-session skill использовать `find_current_jsonl()` из session_archive.py который фильтрует по `sessionId` из последних записей JSONL, а не `ls -t | head -1`. Альтернатива: считывать текущий session_id из Claude Code env переменной или из последней строки JSONL (которая всегда принадлежит текущей сессии).

---

## Сессия 2026-04-03_12_SessionArchive_claude_465d0647 — SA-T018/T031/T035 impl + accept + archive + verify

**Сессия:** `465d0647-b5d7-483f-a7b9-41e0a98bde90`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** /intro → реализация SA-T018 (`_enrich_from_git_status`), SA-T031 (BUG-ARTIFACT-DELETED fix, `base_commit..HEAD`), SA-T035 (BUG-DIFF-SYNTHETIC fix) → /accept → /archive-session → /verify-archive.

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-WRONG-JSONL-ARCHIVED (повторяется) | `ls -t *.jsonl \| head -1` вернул `6f055acb` вместо `465d0647` — 6f055acb был mtime-новее на момент archive-current. Неверная сессия заархивирована с нашим summary | ✅ вручную (переархивировано с --jsonl 465d0647) |
| BUG-SUMMARY-CONTEXT-SPANS-SESSIONS (новый) | summary описывал работу SA-T018/T031/T035, но был применён к session `6f055acb` (обсуждение архитектуры). В контексте Claude одновременно видны оба JSONL → Claude составил summary по видимому контексту, не проверив session_id | ✅ вручную (summary 6f055acb исправлен) |
| BUG-MV-QUOTED-PATHS-WITH-SPACES (повторяется) | task-файлы SA-T018/T031/T035 показаны как `deleted` вместо `moved_from`. Broken artifacts: `docs/3.` (moved_from) + `tasks/SA-T018...` (moved_to). Причина: mv regex `\S+` рвёт путь `docs/3. tasks/` по пробелу | ✅ вручную (исправлены artifacts в SQLite + MD) |

**Исправлено вручную (SQLite + MD):**
- Переархивировано с `--jsonl ~/.claude/projects/.../465d0647...jsonl`: правильная сессия захвачена
- `session_artifacts`: SA-T018/T031/T035 task-файлы исправлены `deleted` → `moved_from`; удалены broken fragments (`docs/3.`, `tasks/SA-T018...`, etc.); добавлены корректные `moved_to` в `Done/`
- `session_artifacts`: BUGS.md исправлен `read` → `modified`
- `session_events`: добавлен `handoff_read`
- `session_tags`: добавлен `skill:archive-session`
- `sessions.summary` для `6f055acb`: исправлен (был "Реализованы SA-T018..." — не та сессия)
- Export MD `465d0647`: обновлены секции Artifacts, Tags, Events

**Новые баги:**

### BUG-SUMMARY-CONTEXT-SPANS-SESSIONS
**Root cause:** VSCode Claude Code extension объединяет несколько JSONL в одно контекстное окно. Когда Claude составляет `--summary` через `/archive-session`, в контексте могут присутствовать сообщения из нескольких session_id. Claude описывает то, что "видит" — а видит он работу из обоих JSONL.
**Воспроизведение:** Продолжить разговор после context-compaction (или открыть два проекта в VSCode) — Claude Code может склеить несколько JSONL в один контекст. Claude опишет summary по всему видимому контексту, а не по выбранному JSONL.
**Рекомендуемый фикс:** В archive-session skill явно инструктировать: "summary описывает ТОЛЬКО работу из JSONL-файла MAIN_JSONL (session_id = последние 8 символов имени файла)". Дополнительно: прочитать первые/последние 5 строк JSONL и подтвердить session_id перед составлением summary.

---

## Сессия 2026-04-03_12_SessionArchive_claude_339f0bc8 — BUGS.md analysis + T022 redesign + normalize done tasks

**Сессия:** `339f0bc8-367f-4726-8fcf-624052b5f5ea`
**Проверено:** 2026-04-03 (verify-archive)
**Контекст:** Анализ root causes роста BUGS.md (279KB, 3348 строк). Архитектурные варианты (tool-call extraction). Ревью задач SA-T016–T023: удалена SA-T022 domain-tags (false diagnosis), SA-T023 переименована в SA-T022 и дополнена BUG-ARTIFACTS-OUTSIDE-CWD + BUG-DIFF-FAILED-EDIT-CAPTURED. Нормализованы заголовки 15 закрытых задач T001–T015 (Выполнено: поле).

| BUG | Симптом в этой сессии | Исправлено |
|-----|----------------------|-----------|
| BUG-WRONG-JSONL (повторяется) | `ls -t \| head -1` выбрал `7a6c847e` (bugs-to-task, соседняя сессия) вместо `339f0bc8` — одинаковый mtime | ✅ вручную (grep по уникальной фразе → правильный JSONL, перезапуск archive) |
| BUG-SKILL-FROM-SKILL-DOC-READ (новый) | Чтение файла `.md` скилла (при /accept читается `accept.md`) создало ложный тег `skill: accept` через detect_skills_used() | ✅ вручную (удалён из SQLite + MD) |
| BUG-SKILL-AFTER-ARCHIVE (повторяется) | `verify-archive` вызван после границы архивации → тег `skill: verify-archive` попал в текущую сессию | ✅ вручную (удалён из SQLite + MD) |
| BUG-MV-SPACE-PATH (повторяется) | `mv "docs/3. tasks/SA-T022..." "docs/3. tasks/Done/..."` → парсер разбил по пробелу: `moved_from: docs/3.` + `moved_to: tasks/SA-T022...` | ✅ вручную (удалены из SQLite + MD) |
| BUG-HANDOFF-DIFF-MULTI-SESSION (повторяется) | Synthetic diff для `SA-HANDOFF.md` включил изменения из 30+ предыдущих сессий | ✅ вручную (заменён на реальный edit_snippet) |

**Root causes:**

**BUG-SKILL-FROM-SKILL-DOC-READ:**
- `detect_skills_used()` ищет паттерн `/path/to/skills/SKILLNAME.md` в Read tool call paths. При запуске /accept скилл сначала читает свой `.md` файл для загрузки инструкций — путь попадает в artifacts → `detect_skills_used()` принимает это за вызов скилла.
- **Fix:** Различать чтение skill `.md` для загрузки инструкций (Read без Skill tool call) и реальный вызов. Доверять только Skill tool calls. Либо: исключить skill `.md` файлы из detect_skills_used() если нет соответствующего Skill tool call с тем же именем.

**BUG-WRONG-JSONL (детализация):**
- Несколько JSONL в project-dir имели одинаковый mtime на уровне секунд (macOS `ls -t` сортирует по целым секундам). При совпадении порядок недетерминирован → `head -1` выбирает произвольный файл.
- **Fix:** После `ls -t | head -1` проверить: grep последних строк JSONL на session_id. Правильный JSONL — тот, в котором session_id последних записей совпадает с текущей сессией Claude Code.
