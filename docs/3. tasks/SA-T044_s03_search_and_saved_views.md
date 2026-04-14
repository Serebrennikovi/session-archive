**Дата:** 2026-04-03
**Статус:** draft
**Спецификация:** docs/2. specifications/SA-S03_review_and_operations_workspace.md

# SA-T044_s03_search_and_saved_views — Поиск по архиву и saved views

## Customer-facing инкремент

Пользователь ищет по истории сессий из браузера и сохраняет повторяемые выборки как готовые views.

---

## Scope

- Full-text search page `/search`
- Индексация effective summary/open issues/messages/artifact paths
- Сохранение текущего filter/search state в `saved_views`
- Быстрый переход к сохранённым views

## Out of scope

- Внешний search engine
- Inline edit результатов поиска
- Analytics dashboard

---

## Как протестировать

1. Открыть `/search`
2. Найти сессию по слову из summary, message и artifact path
3. Сохранить фильтр как saved view
4. Открыть saved view повторно и проверить идентичный результат

---

## Критерии приёмки

1. Поиск возвращает релевантные сессии по summary/messages/artifacts
2. Saved view сохраняет текущий query и набор фильтров
3. Сохранённый view можно открыть из UI повторно
4. Search index обновляется после sync и после курации
