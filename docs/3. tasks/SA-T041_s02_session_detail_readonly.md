**Дата:** 2026-04-03
**Статус:** draft
**Спецификация:** docs/2. specifications/SA-S02_browser_app_foundation.md

# SA-T041_s02_session_detail_readonly — Read-only карточка сессии

## Customer-facing инкремент

Пользователь открывает конкретную сессию в браузере и видит весь её контекст: summary, issues, messages, artifacts, events, tasks и теги.

---

## Scope

- Страница `/sessions/:id`
- Блоки summary/open issues/tags/tasks/events
- Лента сообщений
- Таблица артефактов и collapsible diff/content preview
- Навигация назад к списку и к соседним сессиям того же проекта

## Out of scope

- Редактирование данных
- Review status и queue
- Search и operations

---

## Как протестировать

1. Выполнить SQLite sync
2. Открыть несколько разных `/sessions/:id`
3. Проверить отображение длинных message текстов и diff блоков
4. Перейти назад в список и к соседней сессии того же проекта

---

## Критерии приёмки

1. Страница показывает все связанные сущности выбранной сессии
2. Large message/diff блоки не ломают layout
3. Артефакты и события рендерятся без N+1 деградации на типичной сессии
4. Навигация между списком и карточкой предсказуема
