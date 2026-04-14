**Дата:** 2026-04-03
**Статус:** draft
**Спецификация:** docs/2. specifications/SA-S03_review_and_operations_workspace.md

# SA-T043_s03_manual_summary_curation — Ручная курация summary и open issues

## Customer-facing инкремент

Пользователь может исправить summary и open issues прямо в браузере, а приложение будет показывать curated значения как основную версию сессии.

---

## Scope

- Поля `summary_override`, `open_issues_override`, `review_note`
- Форма курации на странице сессии
- Явное отображение imported vs curated values
- Effective rendering с приоритетом override

## Out of scope

- Редактирование tags/tasks/artifacts/events
- Search и saved views
- Rebuild export после курации

---

## Как протестировать

1. Открыть страницу сессии
2. Изменить summary и open issues
3. Обновить страницу
4. Проверить, что UI показывает curated значения и не теряет imported исходник

---

## Критерии приёмки

1. Пользователь может сохранить override без ручного SQL
2. Effective summary/open issues берутся из override, если он задан
3. Imported значение остаётся доступно для сравнения
4. Курация не ломает повторный SQLite sync
