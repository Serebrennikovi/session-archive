**Дата:** 2026-04-08
**Статус:** draft

# SA-T061 — Skill tag captured from interrupted/unused skill invocation

## Проблема

Когда пользователь запускает `/next` (или любой другой skill), но **сразу прерывает** его и переключается на ручную работу, парсер всё равно записывает `skill: next` в tags. Это создаёт ложное впечатление что сессия выполняла skill `/next`, хотя фактическая работа была ручным code review.

## Как воспроизвести

1. Пользователь вызывает `/next` в чате
2. Claude начинает загружать контекст (HANDOFF, architecture, etc.)
3. Пользователь **прерывает** (Request interrupted by user) до начала реальной работы
4. Пользователь даёт новую инструкцию: "придирчиво отревьювь T049"
5. `archive-current` записывает `skill: next` в tags, хотя `/next` не был выполнен

## Прецедент

Session `ccc065da`: `/next` was invoked via `<command-name>/next</command-name>` but user interrupted before any task was selected. Actual work: manual code review of T049 + fixes to T049/T029. Tag `skill: next` was incorrect.

## Root cause

Парсер детектирует `<command-name>/next</command-name>` в JSONL и безусловно добавляет `skill: next`. Не проверяет был ли skill фактически выполнен или прерван.

## Рекомендуемый фикс

Проверить наличие "Request interrupted by user" или аналогичного маркера в ответе assistant после skill invocation. Если assistant response содержит прерывание до существенного output — не записывать skill tag.

Альтернатива: записывать skill tag только если assistant response после skill invocation содержит >N tool calls (например, >3), что свидетельствует о реальном выполнении.

## Acceptance Criteria

- [ ] Прерванные skills (`<command-name>` + "Request interrupted") не генерируют skill tag
- [ ] Нормально выполненные skills по-прежнему генерируют skill tag
- [ ] Unit-тест: JSONL с прерванным `/next` → нет `skill: next` в tags
