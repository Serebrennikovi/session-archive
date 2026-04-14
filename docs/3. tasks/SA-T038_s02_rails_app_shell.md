**Дата:** 2026-04-03
**Статус:** draft
**Спецификация:** docs/2. specifications/SA-S02_browser_app_foundation.md

# SA-T038_s02_rails_app_shell — Rails app shell и базовая инфраструктура

## Customer-facing инкремент

Пользователь может открыть локальную browser app Session Archive и попасть в предсказуемую web-оболочку вместо чисто CLI-сценария.

---

## Scope

- Создать Rails app в `web/`
- Настроить PostgreSQL, базовый layout, nav и health endpoint
- Зафиксировать базовые модели и routing skeleton для `sessions`
- Добавить `bin/setup` и краткую инструкцию запуска web app

## Out of scope

- Импорт SQLite данных
- Список и карточка сессий с реальным контентом
- Review/search/operations UI

---

## Как протестировать

1. Выполнить `cd web && bin/setup`
2. Запустить `bin/rails server`
3. Открыть `/up`
4. Открыть `/` и проверить, что приложение рендерит layout и навигацию без ошибок

---

## Критерии приёмки

1. В репозитории появляется рабочий Rails app в каталоге `web/`
2. Приложение использует PostgreSQL и поднимается локально
3. Есть базовый layout для будущих страниц архива
4. Есть health endpoint и skeleton routes для `sessions`
