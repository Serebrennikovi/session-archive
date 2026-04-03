# Changelog — Session Archive

Все значимые изменения этого проекта документируются здесь.
Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/).

---

## [Unreleased]

### Добавлено
- 2026-04-03 — SA-T029: EvidenceAccumulator архитектурный слой — `EvidenceAccumulator` класс и `build_evidence()` для структурированного накопления подтверждённых фактов из tool calls; `derive_domain_tags(evidence)` — evidence-based определение доменов по расширениям файлов (без эвристик по директориям); `build_parsed_result` переведён на evidence-слой
- 2026-04-03 — SA-T033: shell-read trace в artifact extractor — файлы, прочитанные через `cat`, `sed`, `head`, `tail`, `rg`, `grep`, `git diff/show/log`, `sqlite3` в Bash tool calls теперь попадают в `session_artifacts` с `action=read`
- 2026-04-03 — SA-T017: archive boundary для artifact extraction — `build_parsed_result` ограничивает tool calls до первого `archive-session` вызова, предотвращая утечку артефактов из предыдущих/соседних сессий
- 2026-04-03 — SA-T036: флаг `manually_reviewed` в таблице `sessions` — защита ручных правок от перезаписи при повторном `archive-current`; флаг `--force` для принудительной перезаписи
- 2026-04-03 — SA-T004: `session_archived` добавляется безусловно в каждую архивированную сессию

### Исправлено
- 2026-04-03 — SA-T029: BUG-TAGS-DOMAIN-DATABASE-FALSE — `derive_domain_tags()` использует только расширения файлов для domain-тегов; убраны ложные паттерны `/(models|schemas)/` для database-домена; теперь `models/user.py` не вызывает тег `domain:database`
- 2026-04-03 — SA-T029: BUG-PARALLEL-SESSION-OVERWRITE / BUG-DIFF-PARALLEL-SESSION — подтверждено и задокументировано: sessionId-фильтрация в `parse_claude_jsonl` + archive_boundary изолируют сессии
- 2026-04-03 — SA-T029: BUG-EVENTS-FALSE-POSITIVE (recurring) — события детектируются только из Bash-вызовов без ошибок (is_error=False), что эквивалентно exit_code=0; задокументировано в EvidenceAccumulator
- 2026-04-03 — SA-T018: BUG-ARTIFACTS-MISSING/BUG-DIFF-MISSING-TRACKED-FILES — `enrich_artifacts` теперь вызывает `_enrich_from_git_status`: все tracked-файлы из `git status --porcelain` (M, A, D, R), не захваченные tool calls, добавляются в `session_artifacts` и получают диффы автоматически
- 2026-04-03 — SA-T031: BUG-ARTIFACT-DELETED — rm-парсер в `extract_artifacts` разрешает относительные пути через cwd перед сравнением с `seen_write`; эфемерные артефакты (created+deleted в одной сессии) корректно исключаются из `session_artifacts`; BUG-DIFF-SPLIT — `_git_diff_for_artifact` теперь использует `base_commit..HEAD` (агрегирует все коммиты сессии)
- 2026-04-03 — SA-T035: BUG-DIFF-WRONG-FILE — `git diff base_commit..HEAD` вместо `git diff base_commit` исключает pre-session uncommitted working-tree изменения из диффов; BUG-DIFF-SYNTHETIC — для modified файлов без baseline `_synthetic_diff_for_artifact` возвращает None вместо `@@ -0,0 +1,N @@`, отдавая приоритет edit_snippet hints
- 2026-04-03 — SA-T036: BUG-RERUN-OVERWRITE — повторный `archive-current` на сессию с `manually_reviewed=1` только обновляет counts, не трогает tags/tasks/events; BUG-ARTIFACT-ACTION-WRONG — Write на git-tracked файл (без предварительного Read) теперь корректно классифицируется как `modified` через `git ls-files`; BUG-ARTIFACT-EVENT-PSEUDO — при миграции схемы `event:*` записи удаляются из `session_artifacts` перед созданием уникального индекса
- 2026-04-03 — SA-T034: BUG-ARTIFACTS-WRONG-SESSION — `parse_claude_jsonl` фильтрует записи по `sessionId`: tool calls из других сессий в том же JSONL-файле больше не попадают в артефакты текущей сессии
- 2026-04-03 — SA-T032: BUG-SUMMARY-FROM-CONTEXT — добавлен `_SUMMARY_META_WORDS` regex в `build_summary`: слова `verify-archive`, `archive-session`, `archive-current`, `session-archive` удаляются из goal-части summary
- 2026-04-03 — SA-T030: BUG-OPEN-ISSUES-FMT — `_strip_markdown()` убирает `**bold**` из open_issues; BUG-MSG-DEDUP-REGRESSION — `_dedupe_adjacent_messages()` применяется перед записью в session_messages во всех code paths; добавлен флаг `--keep-summary` в `archive-current` CLI
- 2026-04-03 — SA-T026: BUG-SUMMARY-MISMATCH/MIXED-PHASES/PARTIAL — `build_summary()` теперь использует только сообщения до archive-boundary (timestamp из первого archive-session tool call); исключает verify-archive / mcp-fix хвост из кандидатов на summary
- 2026-04-03 — SA-T021: BUG-DIFF-FMT/BUG-40 — `_build_unified_diff()` переведён на `splitlines()` без `keepends=True`; двойные `\n` между строками в synthetic diff устранены на уровне root cause; BUG-12 — untracked modified файлы используют earliest Read snapshot как baseline вместо `@@ -0,0 +1,N @@`
- 2026-04-03 — SA-T028: BUG-ARTIFACTS-IDE-OPEN — `<command-message>` сообщения (skill invocations) пропускаются при сканировании task IDs, чтобы примеры в шаблонах не попадали в session_tasks
- 2026-04-03 — SA-T027: BUG-SHELL-VAR-AS-PATH — `$var` пути в `mv` командах фильтруются; BUG-TASK-IDS-BASH-MOVE — task IDs из `Bash mv/cp` команд попадают в session_tasks; BUG-DIFF-DUPLICATE — идентичные diff-сниппеты для одного файла дедуплицируются
- 2026-04-03 — SA-T025: BUG-SLUG-UNDERSCORE-TO-DASH — `_` в PROJECT_SLUG заменяется на `-`; добавлен fuzzy fallback поиск директории по basename проекта
- 2026-04-03 — SA-T024: BUG-SKILL-TAGS-SLASH-COMMAND/TAGS-SKILL-MISSING — скиллы вызванные через `/skillname` (command-name/command-message теги) теперь попадают в skill tags
- 2026-04-03 — SA-T023: BUG-SQLITE-NO-UNIQUE-CONSTRAINT — добавлены UNIQUE indexes для `session_tags`, `session_tasks`, `session_events`, `session_artifacts` — предотвращают дубли при повторной архивации
- 2026-04-03 — SA-T022: BUG-ARTIFACT-WRONG-OP/MISSING-MOVE/OUTSIDE-CWD/FAILED-EDIT — cwd-фильтр (абсолютные пути вне проекта не попадают в артефакты); A+D по одному пути → `modified`; is_error трекинг в parse_claude_jsonl — failed Edit/Write не генерируют хуки в Diffs
- 2026-04-03 — SA-T020: BUG-SKILL-MISSING/TIMING — skill-теги теперь берутся из реальных `Skill` tool calls; archive boundary — Skill calls после `archive-session` исключаются из тегов текущей записи
- 2026-04-03 — SA-T019: BUG-22/24/41 — `event:*` pseudo-пути фильтруются при записи в `session_artifacts`; теперь события живут только в `session_events`
- 2026-04-03 — SA-T016: BUG-OPEN-ISSUES-CONTENT/REASONING-TEXT — убран паттерн `"осталось"` из trigers; добавлен `_OPEN_ISSUES_NOISE_RE` для фильтрации stdout-строк и reasoning-текста из open_issues
- 2026-04-03 — SA-T015: BUG-ARTIFACTS-WRITE-ACTION — Write после Read на тот же файл теперь классифицируется как `modified`, а не `created`
- 2026-04-03 — SA-T014: BUG-TASKS-FROM-TOOL-RESULTS — `<ide_opened_file>` и другие инжектированные теги стрипятся из user-сообщений перед сканированием task IDs
- 2026-04-03 — SA-T013: BUG-14/BUG-21 — соседние дублирующиеся `(role, text)` сообщения удаляются до записи в SQLite и MD-экспорт
- 2026-04-03 — SA-T012: BUG-SKILL-XML/PHANTOM — убрана детекция skill-тегов из `<command-name>` XML в тексте диалога; остаётся только `/skillname` из строк user-сообщений и file-path паттерны
- 2026-04-03 — SA-T011: BUG-ARCHIVE-OVERWRITE — добавлена колонка `summary_manual`; при повторной архивации сохранённый вручную summary не перезаписывается
- 2026-04-03 — SA-T010: BUG-ASSISTANT-TAG-VALUE — тег `assistant` теперь содержит полный model ID (`claude-sonnet-4-6`), а не захардкоженный `claude`
- 2026-04-03 — SA-T009: BUG-DIFF-SCOPE — untracked файлы >300 строк или >200KB получают `diff_source='manual'` без генерации `@@ -0,0 +1,N @@`; error-строка Read tool (`exceeds maximum`) не используется как before-snapshot
- 2026-04-03 — SA-T008: BUG-TAGS-CONTEXT-DRIFT — `detect_domains()` переписан на artifact-based детекцию (только file_path modified/created/deleted артефактов, без сканирования текста диалога); убраны домены `autodev` и `architecture` из автодетекции
- 2026-04-03 — SA-T007: BUG-NEW — mv/rm через Bash tool теперь детектируются как moved_from/moved_to/deleted в session_artifacts
- 2026-04-03 — SA-T007: BUG-ARTIFACTS-WRONG-ACTION — post-check существования файла: если modified/created файл не существует на диске → action=deleted
- 2026-04-03 — SA-T007: Ephemeral артефакты (Write + rm в одной сессии) удаляются из списка
- 2026-04-03 — SA-T006: BUG-27/39/17 — T-номера больше не извлекаются из текста `--summary` (drift из HANDOFF/skill-контекста устранён)
- 2026-04-03 — SA-T006: `extract_task_ids()` теперь сканирует user-сообщения как дополнительный источник явных упоминаний задач
- 2026-04-03 — SA-T006: `tool_result`-контент (Read HANDOFF) не попадает в task_ids (не добавлялся в messages[].text раньше, теперь это явно задокументировано)
- 2026-04-03 — SA-T005: BUG-PROJECT-SLUG-MISMATCH — `sed 's|^/||'` заменён на `sed 's|/|-|g'`, ведущий `/` конвертируется в `-`
- 2026-04-03 — SA-T005: BUG-QUERY-NO-COMMIT — добавлен `conn.commit()` в `cmd_query()`, DML-операции теперь сохраняются
- 2026-04-03 — SA-T004: BUG-31/BUG-EVENTS-FALSE-POSITIVE — `detect_events()` переписан на artifact-based детекцию (убраны text-regex паттерны)
- 2026-04-03 — SA-T004: BUG-EVENTS-MISSING — `session_archived` добавляется безусловно в каждую архивированную сессию
- 2026-04-03 — SA-T004: Убраны phantom events: `review_done`, `task_completed` (нет надёжного сигнала), `handoff_read`/`changelog_read` теперь только из реальных Read tool calls
- 2026-04-03 — SA-T001: BUG-34 — парсинг реальной модели из JSONL (`claude-sonnet-4-6` вместо `claude`)
- 2026-04-03 — SA-T001: BUG-TAGS-XML — убраны мусорные теги из XML-тегов и system-reminder (blocklist + сужение regex)
- 2026-04-03 — SA-T002: BUG-DIFF-DOUBLE-SLASH — убран двойной слеш в заголовках диффов (`a//Users/...` → `a/Users/...`)
- 2026-04-03 — SA-T002: BUG-DIFF-EMPTY-LINES — убраны пустые строки между строками кода в diff-блоках
- 2026-04-03 — SA-T002: BUG-DIFF-UNTRACKED-SCOPE — untracked файлы: diff строится от Read-snapshot сессии, если доступен
- 2026-04-03 — SA-T003: BUG-TASKS-FALSE-POSITIVE — задачи берутся только из Edit/Write к файлам задач (не из текста диалога)
- 2026-04-03 — SA-T003: Спеки (SA-S\d+, ADV-S\d+ и т.д.) убраны из session_tasks

### Изменено
- (пусто)

---

## [1.0.0] — 2026-04-01

### Добавлено
- 2026-04-01 — Документация: создана структура docs/ с SA- префиксом
- 2026-04-01 — SA-architecture.md: полная техническая документация (DB схема, data flow, компоненты)
- 2026-04-01 — SA-HANDOFF.md: состояние проекта, следующие шаги, правила для AI
- 2026-04-01 — SA-CHANGELOG.md: этот файл
- 2026-04-01 — docs/4. guides/: скопированы стандартные гайды (doc_conventions, task_decomposition, specifications)

---

## [0.5.0] — 2026-03-27

### Добавлено
- `session_archive.backup.2026-03-27.py` — резервная копия после рефакторинга
- Поддержка флага `--jsonl <path>` для явного указания пути к JSONL
- Поле `agent_family` в таблице `sessions` с автоопределением (claude/codex/unknown)
- Поле `base_commit` — первый git commit сессии

### Изменено
- `infer_agent_family()` вынесена в отдельную функцию
- Формат экспортного имени: добавлен `agent_family` → `YYYY-MM-DD_repo_agent_hash8.md`

---

## [0.4.0] — 2026-03-26

### Добавлено
- Таблица `session_messages` — полное хранение транскрипта (role, text, timestamp)
- `session_artifacts.diff` и `session_artifacts.diff_source` — unified diff изменений
- `session_artifacts.content` — содержимое файла (до 50 000 символов)
- Индекс `idx_messages_sess`

### Изменено
- `_init_schema()` обновлён с новыми таблицами и колонками

---

## [0.3.0] — 2026-03-25

### Добавлено
- `analyze.py` — аналитические отчёты (summary, projects, tasks, events, domains, timeline, artifacts, models, deep)
- Команда `query <sql>` в `session_archive.py`
- Готовые запросы для Datasette (`datasette_queries.json`)
- Первые ~10 сессий в БД

---

## [0.2.0] — 2026-03-23

### Добавлено
- Частичная поддержка OpenAI Codex JSONL через `detect_jsonl_format()`
- Команда `archive-current` с флагами `--agent`, `--cwd`, `--summary`, `--model`
- `session_events` — отслеживание событий (deploy, tests_run, commit_made, pr_created, handoff_read)
- `session_tasks` — T### задачи, упомянутые в сессии

---

## [0.1.0] — 2026-02-25

### Добавлено
- Первая версия `session_archive.py`
- Команды `parse`, `write`, `stats`
- Схема БД: sessions, session_tags, session_artifacts
- Парсинг Claude Code JSONL (messages, tool_calls)
- Экспорт markdown транскриптов
- Глобальный skill `/archive-session` в `~/.claude/commands/`
- `README.md` с примерами использования
