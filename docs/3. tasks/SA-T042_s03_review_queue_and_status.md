**Дата:** 2026-04-03
**Статус:** draft
**Спецификация:** docs/2. specifications/SA-S03_review_and_operations_workspace.md

# SA-T042_s03_review_queue_and_status — Review queue и triage-статусы

## Customer-facing инкремент

Пользователь видит в браузере очередь сессий на review и может перевести сессию в `reviewed` или `needs_attention` без прямой работы с БД.

---

## Scope

- Поле `review_status` и related timestamps/notes в модели `sessions`
- Страница `/reviews/queue`
- Фильтры по статусу и проекту
- Массово или точечно менять статус сессии

## Out of scope

- Редактирование summary/open issues
- Full-text search
- Запуск sync/rebuild jobs

---

## Как протестировать

1. Открыть `/reviews/queue`
2. Перевести одну сессию в `reviewed`, другую в `needs_attention`
3. Отфильтровать очередь по статусу
4. Проверить, что изменения видны в списке и на странице сессии

---

## Критерии приёмки

1. Все новые импортированные сессии имеют статус `pending`
2. Статус меняется из UI без ручного SQL
3. Очередь корректно фильтруется по статусам
4. Для `needs_attention` можно сохранить причину или note
