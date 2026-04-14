# Спецификация: Review и operations workspace в browser app

**ID:** SA-S03
**Статус:** draft
**Версия:** 1.0
**Дата:** 2026-04-03

---

## Цель

Сделать browser app основным рабочим интерфейсом для архива: не только смотреть сессии, но и triage-ить их, вручную уточнять summary/open issues, искать по истории и запускать операционные действия без прямой работы с SQLite, markdown и shell-командами.

Этот этап опирается на SA-S02 и сохраняет split architecture: Python остаётся источником raw-архивации, а Rails становится слоем review, поиска и ежедневных операций. Инкремент для пользователя: после открытия браузера он может найти нужную сессию, пометить её reviewed, исправить итоговое резюме и запустить sync/rebuild без ручной возни с БД.

---

## Scope

### Входит:

- Review queue по статусам `pending`, `reviewed`, `needs_attention`
- Ручная курация `summary`, `open_issues` и review note на странице сессии
- Full-text search по summary, open issues, messages и artifact paths/content
- Saved views для часто используемых фильтров
- Operations page для sync из SQLite и rebuild markdown export по выбранной сессии
- История операций и их статусы в UI

### Не входит:

- Полный rewrite ingestion/parser слоя на Ruby
- Редактирование `session_artifacts`, `session_tasks`, `session_events` построчно из UI
- Замена `/archive-session` или автоматический запуск архивирования из браузера
- Внешняя авторизация, роли, командная совместная работа

---

## Архитектура и структура

### Принцип curation-first

- Imported data продолжает приходить из SQLite sync
- Curated data хранится в PostgreSQL рядом с imported snapshot
- UI всегда показывает effective value:
  - `summary_override` если есть, иначе imported `summary`
  - `open_issues_override` если есть, иначе imported `open_issues`

### Новые компоненты

- `web/app/controllers/reviews_controller.rb` — review queue и triage
- `web/app/controllers/search_controller.rb` — global search и saved views
- `web/app/controllers/operations_controller.rb` — sync/rebuild actions
- `web/app/services/search/session_search_document.rb` — сбор search document
- `web/app/jobs/sqlite_sync_job.rb` — sync из SQLite
- `web/app/jobs/rebuild_export_job.rb` — rebuild markdown export через текущий Python CLI

### Поток данных

```text
SQLite sync
  -> imported sessions in PostgreSQL
  -> user opens review queue
  -> sets review status / adds override
  -> search uses effective document
  -> operations page triggers sync/rebuild jobs
```

---

## Изменения в БД

### Изменения таблицы `sessions`

```sql
ALTER TABLE sessions ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE sessions ADD COLUMN reviewed_at TIMESTAMP;
ALTER TABLE sessions ADD COLUMN review_note TEXT;
ALTER TABLE sessions ADD COLUMN summary_override TEXT;
ALTER TABLE sessions ADD COLUMN open_issues_override JSONB;
ALTER TABLE sessions ADD COLUMN needs_attention_reason TEXT;
ALTER TABLE sessions ADD COLUMN search_text TEXT;
ALTER TABLE sessions ADD COLUMN search_tsv tsvector;
```

### Новая таблица saved views

```sql
saved_views (
  id          BIGSERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  scope_type  TEXT NOT NULL,
  query_json  JSONB NOT NULL,
  pinned      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMP NOT NULL,
  updated_at  TIMESTAMP NOT NULL
);
```

### Расширение истории операций

`archive_import_runs` расширяется до общего лога операций:

```sql
ALTER TABLE archive_import_runs ADD COLUMN operation_type TEXT NOT NULL DEFAULT 'sqlite_sync';
ALTER TABLE archive_import_runs ADD COLUMN session_id TEXT;
ALTER TABLE archive_import_runs ADD COLUMN triggered_from_ui BOOLEAN NOT NULL DEFAULT FALSE;
```

### Индексы

- `idx_sessions_review_status(review_status, created_at DESC)`
- `idx_sessions_search_tsv USING GIN(search_tsv)`
- `idx_saved_views_scope(scope_type, pinned)`
- `idx_archive_import_runs_operation_type(operation_type, started_at DESC)`

### Правило effective search document

`search_tsv` строится из:

- effective summary
- effective open issues
- `repo_name`, `branch`, `ai_model`
- текстов `session_messages`
- `file_path` и ограниченного фрагмента `content`/`diff` из `session_artifacts`

---

## Веб и HTTP интерфейс

### Веб-маршруты

- `GET /reviews/queue`
- `PATCH /sessions/:id/review`
- `PATCH /sessions/:id/curation`
- `GET /search`
- `POST /saved_views`
- `PATCH /saved_views/:id`
- `GET /operations`
- `POST /operations/sqlite_sync`
- `POST /operations/rebuild_export`

### Поведение операций

- `sqlite_sync` ставит `SqliteSyncJob` в очередь
- `rebuild_export` ставит `RebuildExportJob` для конкретной `session_id`
- UI не блокируется: пользователь видит статус `queued/running/succeeded/failed`

---

## Acceptance Criteria / DoD

- [ ] `/reviews/queue` показывает pending и problematic sessions
- [ ] Пользователь может менять `review_status` и оставлять `review_note`
- [ ] Пользователь может вручную задать `summary_override` и `open_issues_override`
- [ ] На странице сессии effective summary/open issues берутся из override, если он задан
- [ ] `/search?q=...` ищет по summary, messages и artifacts
- [ ] Пользователь может сохранить текущий search/filter как saved view
- [ ] `/operations` позволяет запустить sync и rebuild export, а история операций отображает статус и ошибки

---

## Тест-план

1. Импортировать данные через SA-S02 flow
2. Открыть `/reviews/queue` и убедиться, что все новые сессии имеют `pending`
3. Для одной сессии установить `reviewed`, для другой `needs_attention`
4. На странице сессии изменить summary и open issues, обновить страницу и проверить приоритет override
5. Выполнить поиск по слову из message и по пути артефакта
6. Сохранить фильтр как saved view и открыть его повторно
7. Запустить `sqlite_sync` и `rebuild_export` из `/operations`, проверить историю и статус jobs

---

## Зависимости и интеграции

- Требует [SA-S02_browser_app_foundation.md](SA-S02_browser_app_foundation.md)
- Использует текущий Python CLI для rebuild export
- Использует PostgreSQL full-text search без обязательного внешнего search engine

---

## Риски и ограничения

- Curated override fields создают второй слой истины, его нужно явно показывать в UI
- `search_tsv` нужно обновлять после sync и после ручной курации, иначе поиск станет stale
- Rebuild export через Python subprocess должен быть идемпотентным и безопасным для `manually_reviewed`
- Без построчного editor-а для артефактов часть verify-сценариев всё ещё останется shell-first

---

## Задачи

1. [SA-T042](../3.%20tasks/SA-T042_s03_review_queue_and_status.md) — review queue и triage-статусы
   Требует: SA-S02
   Блокирует: SA-T043, SA-T044, SA-T045
2. [SA-T043](../3.%20tasks/SA-T043_s03_manual_summary_curation.md) — ручная курация summary и open issues
   Требует: SA-T042
3. [SA-T044](../3.%20tasks/SA-T044_s03_search_and_saved_views.md) — поиск и saved views
   Требует: SA-T042
   Можно параллельно с: SA-T043
4. [SA-T045](../3.%20tasks/SA-T045_s03_sync_and_rebuild_operations.md) — operations page и фоновые jobs
   Требует: SA-T042
   Можно параллельно с: SA-T043, SA-T044

---

## Связанные документы

- Архитектура: [SA-architecture.md](../SA-architecture.md)
- Handoff: [SA-HANDOFF.md](../SA-HANDOFF.md)
- Зависит от: [SA-S02_browser_app_foundation.md](SA-S02_browser_app_foundation.md)
- Блокирует: следующую спеку по deep curation и browser-side verify
