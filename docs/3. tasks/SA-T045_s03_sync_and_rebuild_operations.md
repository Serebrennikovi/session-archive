**Дата:** 2026-04-03
**Статус:** draft
**Спецификация:** docs/2. specifications/SA-S03_review_and_operations_workspace.md

# SA-T045_s03_sync_and_rebuild_operations — Operations page для sync и rebuild

## Customer-facing инкремент

Пользователь запускает sync архива и rebuild markdown export из браузера и видит историю операций со статусами и ошибками.

---

## Scope

- Страница `/operations`
- Кнопка запуска `sqlite_sync`
- Кнопка запуска `rebuild_export` для выбранной сессии
- История операций с состояниями `queued/running/succeeded/failed`

## Out of scope

- Запуск `/archive-session` из браузера
- Browser-side verify editor для артефактов
- Background orchestration за пределами локальной машины

---

## Как протестировать

1. Открыть `/operations`
2. Запустить sync из SQLite
3. Запустить rebuild export для конкретной сессии
4. Проверить, что статусы и ошибки отображаются в истории операций

---

## Критерии приёмки

1. Sync и rebuild запускаются из UI как фоновые jobs
2. Пользователь видит текущий статус операции без чтения логов в shell
3. Ошибки выполнения сохраняются и отображаются в истории
4. Rebuild export не уничтожает curated данные и не нарушает `manually_reviewed` semantics
