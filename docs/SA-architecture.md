# Architecture: Session Archive

> Система сохранения и анализа диалогов с AI-ассистентами.
> **Статус:** active
> **Последнее обновление:** 2026-04-03 (v1.1 — EvidenceAccumulator, archive_boundary, manually_reviewed guard, git-status enrichment)

---

## Диаграмма системы

```
┌─────────────────────────────────────────────────────────────────┐
│                         Локальная машина                        │
│                                                                 │
│  Claude Code / OpenAI Codex                                     │
│  ┌─────────────────────────────┐                                │
│  │  AI Session                 │                                │
│  │  ~/.claude/projects/**/*.jsonl  (Claude)                     │
│  │  ~/.codex/**/*.jsonl            (Codex)                      │
│  └───────────┬─────────────────┘                                │
│              │ /archive-session  (Claude Code skill)            │
│              ▼                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  session_archive.py  (CLI)                              │   │
│  │                                                         │   │
│  │  archive-current                                        │   │
│  │    ├── detect_jsonl_format()  → claude | codex          │   │
│  │    ├── parse_claude_jsonl()                             │   │
│  │    │   or parse_codex_jsonl()                          │   │
│  │    ├── extract artifacts, events, tasks, tags           │   │
│  │    └── write_session_to_db()                           │   │
│  │         └── export_markdown()                          │   │
│  │                                                         │   │
│  │  parse   → stdout JSON (for skill integration)          │   │
│  │  write   → stdin JSON → DB + markdown                   │   │
│  │  stats   → stdout текстовая статистика                  │   │
│  │  query   → произвольный SELECT → stdout JSON            │   │
│  └──────────┬──────────────────────────────────────────────┘   │
│             │                     │                              │
│             ▼                     ▼                              │
│  ┌──────────────────┐   ┌─────────────────────────────┐        │
│  │  data/sessions.db│   │  data/exports/              │        │
│  │  (SQLite, WAL)   │   │  YYYY-MM-DD_repo_agent_     │        │
│  │                  │   │  {hash}.md                  │        │
│  └──────────────────┘   └─────────────────────────────┘        │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  analyze.py  (аналитика)                             │      │
│  │  python3 analyze.py [summary|projects|tasks|...]     │      │
│  └──────────────────────────────────────────────────────┘      │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────┐                               │
│  │  Datasette (опционально)     │                               │
│  │  datasette data/sessions.db  │                               │
│  │  http://localhost:8001       │                               │
│  └──────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Компоненты

### session_archive.py — основной CLI

Единственная точка входа для записи сессий. Без внешних зависимостей (только stdlib Python 3.x).

**Команды:**

| Команда | Описание |
|---------|----------|
| `parse <jsonl_path>` | Парсит JSONL → stdout JSON со структурой сессии |
| `write <metadata_json_file>` | Пишет сессию в БД + экспортирует markdown |
| `archive-current [flags]` | Находит текущую сессию, собирает metadata, пишет в БД |
| `stats` | Краткая статистика по всем сессиям |
| `query <sql>` | Произвольный SELECT к БД → stdout JSON |

**Флаги `archive-current`:**

| Флаг | Дефолт | Описание |
|------|--------|----------|
| `--agent auto\|claude\|codex` | auto | Тип агента (auto = autodetect) |
| `--cwd <path>` | текущий каталог | Рабочая директория |
| `--summary <text>` | — | Краткое резюме сессии |
| `--model <model>` | — | Название AI модели |
| `--jsonl <path>` | autodetect | Путь к JSONL файлу |

### analyze.py — аналитика

Отчёты поверх `sessions.db`. Только чтение, без зависимостей.

| Команда | Что показывает |
|---------|---------------|
| `summary` | Общее число сессий, сообщений, tool calls |
| `projects` | Активность по проектам |
| `tasks` | Топ T### задач (сколько сессий) |
| `events` | Частота событий (deploy, tests_run...) |
| `domains` | Самые часто трогаемые домены кода |
| `timeline` | Активность по дням |
| `artifacts` | Самые изменяемые файлы |
| `models` | Использование AI моделей |
| `deep <project>` | Детальный отчёт по конкретному проекту |

---

## Схема базы данных

```sql
sessions (
  id               TEXT PRIMARY KEY,   -- session UUID
  created_at       TEXT NOT NULL,       -- ISO8601 UTC
  ended_at         TEXT,
  project_path     TEXT,               -- /abs/path/to/project
  repo_name        TEXT,               -- название репозитория
  branch           TEXT,               -- git ветка
  base_commit      TEXT,               -- первый git commit в сессии
  agent_family     TEXT DEFAULT 'unknown',  -- claude | codex | unknown
  ai_model         TEXT,               -- claude-sonnet-4-6, gpt-4o...
  summary          TEXT,               -- краткое резюме сессии (авто)
  summary_manual   TEXT,               -- ручное резюме (приоритет над summary)
  open_issues      TEXT,               -- нерешённые вопросы
  msg_count        INTEGER DEFAULT 0,  -- всего сообщений
  user_msg_count   INTEGER DEFAULT 0,  -- сообщений от пользователя
  tool_call_count  INTEGER DEFAULT 0,  -- всего tool calls
  export_path      TEXT,               -- путь к .md транскрипту
  raw_jsonl_path   TEXT,               -- путь к исходному JSONL
  manually_reviewed INTEGER DEFAULT 0  -- 1 = сессия вручную исправлена, защита от перезаписи
)

session_tags (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  category    TEXT NOT NULL,   -- project | domain | model | custom
  value       TEXT NOT NULL
)

session_tasks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  task_id     TEXT NOT NULL,   -- T001, T002... (из текста сессии)
  actions     TEXT             -- что делали: created|modified|mentioned
)

session_artifacts (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  file_path   TEXT NOT NULL,
  action      TEXT,            -- created | modified | deleted | moved | read
  is_code     INTEGER DEFAULT 0,
  is_doc      INTEGER DEFAULT 0,
  content     TEXT,            -- содержимое файла (до 50 000 символов)
  diff        TEXT,            -- unified diff (до 30 000 символов)
  diff_source TEXT             -- откуда взят diff
)

session_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  event_type  TEXT NOT NULL,   -- deploy | tests_run | commit_made | pr_created | handoff_read...
  detail      TEXT
)

session_messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  role        TEXT NOT NULL,   -- user | assistant | tool
  text        TEXT NOT NULL,
  timestamp   TEXT
)
```

**Индексы:**

```sql
idx_tags_session    ON session_tags(session_id)
idx_tags_cat        ON session_tags(category, value)
idx_tasks_id        ON session_tasks(task_id)
idx_artifacts_path  ON session_artifacts(file_path)
idx_events_type     ON session_events(event_type)
idx_sessions_proj   ON sessions(project_path)
idx_sessions_date   ON sessions(created_at)
idx_sessions_agent  ON sessions(agent_family)
idx_messages_sess   ON session_messages(session_id)
```

**Режим:** WAL (Write-Ahead Log) + `foreign_keys=ON`.
**Эволюция схемы:** через `_ensure_column()` — безопасное добавление колонок без ломающих миграций.

---

## Формат данных: детектирование JSONL

Автоопределение формата через `detect_jsonl_format()`:

| Признак | Формат |
|---------|--------|
| `entry.get("message")` или `gitBranch` или `cwd` | claude |
| type in `response_item`, `turn_context`, `event_msg` | codex |
| `type == session_meta` + originator starts with "codex" | codex |
| Дефолт | claude |

### Claude Code JSONL

Путь: `~/.claude/projects/<project_hash>/<session_id>.jsonl`

Каждая строка — JSON объект:
- `type` — тип записи
- `timestamp` — ISO8601
- `gitBranch`, `cwd`, `sessionId`, `gitCommit`
- `message` — {role, content: []}
- `content[].type` — text | tool_use | tool_result

### OpenAI Codex JSONL

Путь: `~/.codex/<session_id>.jsonl`

- `type`: `response_item` | `turn_context` | `event_msg` | `session_meta`
- Транскрипт парсится с ограниченной точностью (частичная поддержка)

---

## Классификация артефактов

```python
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".go",
            ".rs", ".java", ".rb", ".php", ".sql", ".c", ".cpp", ".h", ".cs"}

DOC_EXT  = {".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".toml", ".csv"}

DIFF_ACTIONS = {"created", "modified", "deleted", "moved"}

MAX_ARTIFACT_CONTENT = 50_000   # символов
MAX_ARTIFACT_DIFF    = 30_000   # символов
```

---

## Архитектура извлечения данных (SA-T029)

### Archive Boundary

`_find_archive_boundary_idx(tool_calls)` возвращает индекс первого вызова `/archive-session` (Skill) или `archive-current` (Bash) в списке tool_calls. Все извлечения (артефакты, теги, задачи) применяются только к tool_calls **до** этой границы — чтобы не захватывать контекст предыдущих сессий, которые были заархивированы в рамках текущего разговора.

```
tool_calls[0..archive_boundary_idx]  ← только эти для артефактов/тегов
tool_calls[0..N]                     ← все для task_ids (задачи из всей сессии)
```

### EvidenceAccumulator

Класс `EvidenceAccumulator` — единый проход по `tool_calls` для сбора структурированных фактов. Используется как источник правды для дальнейших derivers (domain tags, skill tags, task extraction).

```python
class EvidenceAccumulator:
    write_paths: list[str]       # файлы, записанные через Write/Edit/NotebookEdit
    read_paths: set[str]         # файлы, прочитанные через Read (полные чтения)
    bash_calls: list[(cmd, is_error)]  # каждый Bash/exec_command вызов
    skill_names: list[str]       # skill names из Skill tool calls до archive_boundary
    task_file_edits: list[str]   # task IDs из путей файлов Edit/Write
    archive_boundary: int        # индекс первого archive-session call
    cwd: str                     # рабочая директория
```

Преимущество: вместо нескольких независимых regex-проходов по тексту — один проход по структурированным tool calls. Резко снижает context drift (домены и теги выводятся из реальных действий, не из слов в диалоге).

### Git-Status Enrichment

`_enrich_from_git_status(artifacts, project_root)` (SA-T018): после извлечения артефактов из tool_calls — добавляет файлы из `git status`, которые были изменены через Bash или внешние инструменты, не захваченные парсингом tool calls. Применяется только к tracked файлам в рамках project_root.

### Manually Reviewed Guard

При повторной архивации (`archive-current` на уже существующей сессии):
- если `manually_reviewed=1` → пересчитываются только counts и ai_model; tags/tasks/events/messages не трогаются
- если передан `--summary`, он записывается в `summary_manual` даже для manually_reviewed сессий
- `--force` снимает защиту, перезаписывает всё

`summary_manual` (если задан) имеет приоритет над авто-генерированным `summary` во всех выводах (markdown экспорт, stats).

---

## Интеграция с Claude Code (skill)

Сохранение сессии вызывается через skill `/archive-session`, определённый в:
- `~/.claude/commands/archive-session.md` — глобальный навык

Skill вызывает `session_archive.py archive-current --cwd <project_path> --summary "<text>"`.

Схема вызова в конце сессии:
```
Пользователь: /archive-session
    → Claude читает HANDOFF, собирает summary
    → claude запускает: python3 /path/to/session_archive.py archive-current ...
    → получает: {"session_id": "...", "export_path": "..."}
    → выводит статус
```

---

## Переменные окружения

| Переменная | Дефолт | Описание |
|------------|--------|----------|
| `SESSION_ARCHIVE_DB_PATH` | `<script_dir>/data/sessions.db` | Путь к SQLite базе |
| `SESSION_ARCHIVE_EXPORT_DIR` | `<script_dir>/data/exports` | Папка для markdown экспортов |

---

## Структура файлов проекта

```
12_SessionArchive/
├── session_archive.py              ← основной CLI
├── analyze.py                      ← аналитика
├── BUGS.md                         ← известные баги
├── README.md                       ← обзор для разработчиков
├── data/
│   ├── sessions.db                 ← SQLite БД (не в git)
│   └── exports/
│       └── YYYY-MM-DD_repo_agent_hash.md
├── docs/
│   ├── SA-architecture.md          ← этот файл
│   ├── SA-HANDOFF.md               ← состояние проекта
│   ├── SA-CHANGELOG.md             ← история изменений
│   ├── 1. business requirements/
│   ├── 2. specifications/
│   ├── 3. tasks/
│   │   └── Done/
│   ├── 4. guides/
│   │   ├── doc_conventions.md
│   │   ├── task_decomposition_guide.md
│   │   └── specifications_guide.md
│   ├── 5. unsorted/
│   └── 6. backlog/
└── ~/ (глобальные файлы Claude)
    └── .claude/commands/archive-session.md
```

---

## Поддерживаемые агенты

| Среда | Поддержка | Примечание |
|-------|-----------|------------|
| Claude Code (CLI) | Полная | JSONL парсится автоматически |
| OpenAI Codex | Частичная | Транскрипт пустой, метаданные вручную |
| Любой AI чат | Частичная | Только метаданные |

---

## Ключевые архитектурные решения

### Почему SQLite (не PostgreSQL, не файлы)

- Локальная инфраструктура — нет необходимости в сервере БД
- SQLite идеален для append-only log-like данных
- WAL режим позволяет конкурентное чтение во время записи
- Datasette даёт полноценный web UI без дополнительного кода
- Простое резервное копирование: `cp sessions.db sessions.db.bak`

### Почему нет зависимостей (чистый stdlib)

- `session_archive.py` использует только stdlib Python 3.x
- Работает без `pip install` на любой машине с Python 3
- Критично для вызова из hooks и scripts без виртуального окружения

### Почему markdown экспорты (а не только БД)

- Читаемые транскрипты для human review
- Можно передать другому человеку без доступа к БД
- Служат источником для full-text search вне SQLite

### Эволюция схемы через `_ensure_column()`

Вместо нумерованных миграций — `ALTER TABLE ADD COLUMN IF NOT EXISTS`.
Это позволяет обновлять скрипт без ручных миграций на всех машинах.
Минус: нет rollback, нет down-миграций. Приемлемо для solo-проекта.

---

## Datasette (опциональный веб-интерфейс)

```bash
pip install datasette
datasette data/sessions.db --metadata datasette_queries.json
# http://localhost:8001
```

Готовые запросы хранятся в `datasette_queries.json` рядом с `sessions.db`.
