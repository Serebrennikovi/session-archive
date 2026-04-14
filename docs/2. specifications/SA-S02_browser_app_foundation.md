# Спецификация: Browser-first foundation на Rails

**ID:** SA-S02
**Статус:** draft
**Версия:** 1.0
**Дата:** 2026-04-03

---

## Цель

Перевести Session Archive из CLI-only инструмента в browser-first приложение для повседневной работы с историей сессий. На этом этапе не переписываем ingestion-ядро: текущий Python CLI продолжает парсить JSONL и писать архив, а новая Rails app даёт структурированный web workspace поверх уже накопленных данных.

Главный инкремент: пользователь открывает браузер и получает нормальный каталог сессий и страницу конкретной сессии вместо работы через SQLite, markdown-экспорты и один мегаскрипт. Это одновременно решает UX-проблему и создаёт новую файловую структуру проекта, в которой UI, импорт и доменная модель живут раздельно.

---

## Scope

### Входит:

- Новый Rails 8.1 app в каталоге `web/`
- PostgreSQL как отдельная БД web app
- Read model в PostgreSQL, зеркалирующая текущий архив: `sessions`, `session_tags`, `session_tasks`, `session_artifacts`, `session_events`, `session_messages`
- Идемпотентный sync из текущей SQLite БД `data/sessions.db` в PostgreSQL
- Read-only web routes: список сессий и страница сессии
- Базовые фильтры и сортировка по проекту, ветке, агенту, модели и дате

### Не входит:

- Переписывание `session_archive.py` или JSONL parser на Ruby
- Замена `/archive-session` и текущего CLI pipeline
- Редактирование данных архива из браузера
- Full-text search, saved views, review queue и операции rebuild/sync из UI
- Мультипользовательский режим, внешняя auth, деплой в интернет

---

## Архитектура и структура

### Принцип перехода

Переход делается через split architecture:

- Python остаётся ingestion/write path
- Rails становится browser/read path
- SQLite остаётся текущим operational source для архивации
- PostgreSQL становится web read model для UI

### Новая структура репозитория

```text
12_SessionArchive/
├── session_archive.py
├── analyze.py
├── data/
│   └── sessions.db
├── docs/
└── web/
    ├── app/
    ├── config/
    ├── db/
    ├── lib/
    └── bin/
```

### Поток данных

```text
/archive-session
  -> session_archive.py
  -> SQLite data/sessions.db
  -> Rails sync service
  -> PostgreSQL web DB
  -> /sessions, /sessions/:id
```

### Компоненты

- `web/app/models/*` — Rails models для read model
- `web/app/controllers/sessions_controller.rb` — список и карточка сессии
- `web/app/services/archive/sqlite_sync.rb` — импорт SQLite -> PostgreSQL
- `web/lib/tasks/archive.rake` — ручной запуск sync через `bin/rails`
- `web/app/views/sessions/*` — Hotwire/Turbo-compatible read-only UI

---

## Изменения в БД

Новая отдельная PostgreSQL схема внутри Rails app.

### Таблицы

```sql
sessions (
  id                TEXT PRIMARY KEY,
  created_at        TIMESTAMP NOT NULL,
  ended_at          TIMESTAMP,
  project_path      TEXT,
  repo_name         TEXT,
  branch            TEXT,
  base_commit       TEXT,
  agent_family      TEXT NOT NULL,
  ai_model          TEXT,
  summary           TEXT,
  open_issues       JSONB,
  msg_count         INTEGER NOT NULL DEFAULT 0,
  user_msg_count    INTEGER NOT NULL DEFAULT 0,
  tool_call_count   INTEGER NOT NULL DEFAULT 0,
  export_path       TEXT,
  raw_jsonl_path    TEXT,
  manually_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
  imported_at       TIMESTAMP NOT NULL
);

session_tags (
  id         BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  category   TEXT NOT NULL,
  value      TEXT NOT NULL
);

session_tasks (
  id         BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  task_id    TEXT NOT NULL,
  actions    TEXT
);

session_artifacts (
  id          BIGSERIAL PRIMARY KEY,
  session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  file_path   TEXT NOT NULL,
  action      TEXT,
  is_code     BOOLEAN NOT NULL DEFAULT FALSE,
  is_doc      BOOLEAN NOT NULL DEFAULT FALSE,
  content     TEXT,
  diff        TEXT,
  diff_source TEXT
);

session_events (
  id         BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  detail     TEXT
);

session_messages (
  id         BIGSERIAL PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  role       TEXT NOT NULL,
  text       TEXT NOT NULL,
  timestamp  TIMESTAMP
);

archive_import_runs (
  id                BIGSERIAL PRIMARY KEY,
  source_path       TEXT NOT NULL,
  source_db_mtime   TIMESTAMP,
  status            TEXT NOT NULL,
  sessions_seen     INTEGER NOT NULL DEFAULT 0,
  sessions_upserted INTEGER NOT NULL DEFAULT 0,
  started_at        TIMESTAMP NOT NULL,
  finished_at       TIMESTAMP,
  error_text        TEXT
);
```

### Индексы

- `idx_sessions_repo_created_at(repo_name, created_at DESC)`
- `idx_sessions_agent_created_at(agent_family, created_at DESC)`
- `idx_session_tags_category_value(category, value)`
- `idx_session_tasks_task_id(task_id)`
- `idx_session_artifacts_path(file_path)`
- `idx_session_events_type(event_type)`
- `idx_session_messages_session_timestamp(session_id, timestamp)`

### Правило синхронизации

- Sync идемпотентный: повторный импорт той же SQLite БД не создаёт дубли
- Child rows для одной сессии пересобираются atomically внутри транзакции
- Rails read model не пишет обратно в SQLite

---

## Веб и CLI интерфейс

### Веб-маршруты

- `GET /` -> redirect на `/sessions`
- `GET /sessions`
- `GET /sessions/:id`
- `GET /up` -> health endpoint Rails app

### Служебная команда sync

```bash
cd web
bin/rails archive:sync_sqlite SOURCE_DB=../data/sessions.db
```

**Аргументы:**

- `SOURCE_DB` — путь к SQLite архиву

**Поведение:**

- читает все сессии из SQLite
- делает upsert в PostgreSQL
- пишет результат в `archive_import_runs`

---

## Acceptance Criteria / DoD

- [ ] Rails app в `web/` запускается локально и открывается в браузере
- [ ] `bin/rails archive:sync_sqlite SOURCE_DB=../data/sessions.db` импортирует данные без дублей
- [ ] `/sessions` показывает список сессий из PostgreSQL
- [ ] Фильтры по `repo_name`, `branch`, `agent_family`, `ai_model`, диапазону дат работают
- [ ] `/sessions/:id` показывает summary, open issues, tags, tasks, events, artifacts и messages
- [ ] Повторный sync корректно обновляет изменившиеся сессии

---

## Тест-план

1. Поднять PostgreSQL и запустить `cd web && bin/setup`
2. Выполнить `bin/rails archive:sync_sqlite SOURCE_DB=../data/sessions.db`
3. Открыть `/sessions` и проверить, что число записей совпадает с SQLite
4. Отфильтровать список по проекту и агенту
5. Открыть 2-3 разные сессии и проверить наличие связанных сообщений, тегов, задач, артефактов и событий
6. Повторно выполнить sync и убедиться, что количество child rows не удваивается

---

## Зависимости и интеграции

- Использует существующий SQLite архив `data/sessions.db` как вход
- Не меняет текущий Python ingestion pipeline
- Блокирует SA-S03: review/search/operations workspace

---

## Риски и ограничения

- Возникает dual-storage схема: SQLite и PostgreSQL могут расходиться при неаккуратном sync
- Rails app потребует отдельного локального runtime: Ruby, Bundler, PostgreSQL
- Очень длинные `messages` и `diff` поля нужно аккуратно рендерить в UI, чтобы не положить страницу
- До появления UI-операций sync остаётся ручной командой

---

## Задачи

1. [SA-T038](../3.%20tasks/SA-T038_s02_rails_app_shell.md) — Rails app shell и базовая инфраструктура
   Блокирует: SA-T039, SA-T040, SA-T041
2. [SA-T039](../3.%20tasks/SA-T039_s02_sqlite_to_postgres_sync.md) — SQLite -> PostgreSQL sync read model
   Требует: SA-T038
   Блокирует: SA-T040, SA-T041
3. [SA-T040](../3.%20tasks/SA-T040_s02_sessions_index.md) — список сессий и фильтры
   Требует: SA-T039
4. [SA-T041](../3.%20tasks/SA-T041_s02_session_detail_readonly.md) — read-only карточка сессии
   Требует: SA-T039
   Можно параллельно с: SA-T040

---

## Связанные документы

- Архитектура: [SA-architecture.md](../SA-architecture.md)
- Handoff: [SA-HANDOFF.md](../SA-HANDOFF.md)
- Зависит от: нет
- Блокирует: [SA-S03_review_and_operations_workspace.md](SA-S03_review_and_operations_workspace.md)
