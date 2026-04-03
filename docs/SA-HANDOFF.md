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

**Пользователь:** И.С. (solo проект, личный инструмент)

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

---

## Следующие шаги (backlog)

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
- **[SA-T037](3.%20tasks/SA-T037_s01_context-window-whitelist.md)** — Реализовать SA-S01: context-window whitelist для session boundary (`--tool-ids` в archive-current + обновление скилла) 🔜
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
- Поиск по тексту сессий (FTS5 в SQLite) — см. спека [SA-S02](2.%20specifications/) (будущая)
- Тег-система: ручная разметка сессий
- Экспорт конкретной сессии по ID

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
