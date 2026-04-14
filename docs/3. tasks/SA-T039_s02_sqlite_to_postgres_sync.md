**Дата:** 2026-04-03
**Статус:** draft
**Спецификация:** docs/2. specifications/SA-S02_browser_app_foundation.md

# SA-T039_s02_sqlite_to_postgres_sync — Идемпотентный sync SQLite архива в PostgreSQL

## Customer-facing инкремент

Пользователь получает в browser app актуальные данные из существующего архива без ручного копирования SQLite таблиц.

---

## Scope

- Создать read model таблицы в PostgreSQL для session archive
- Реализовать `archive:sync_sqlite` для импорта `data/sessions.db`
- Сделать идемпотентный upsert по `session_id`
- Вести лог запусков в `archive_import_runs`

## Out of scope

- UI для запуска sync
- Full-text search и review-поля
- Переписывание Python ingestion

---

## Как протестировать

1. Выполнить `cd web && bin/rails archive:sync_sqlite SOURCE_DB=../data/sessions.db`
2. Проверить число записей в `sessions` и child tables
3. Повторно выполнить ту же команду
4. Убедиться, что дубли не появились, а `archive_import_runs` содержит оба запуска

---

## Критерии приёмки

1. Sync импортирует `sessions`, `session_tags`, `session_tasks`, `session_artifacts`, `session_events`, `session_messages`
2. Повторный sync не создаёт дублей
3. Ошибки запуска фиксируются в `archive_import_runs`
4. Child rows одной сессии пересобираются атомарно
