**Дата:** 2026-04-14
**Статус:** draft
**Severity:** MEDIUM
**Воспроизведение:** session 84b0f69d (autodev-v2, 2026-04-14)

# SA-T089: Tasks false positive — task IDs extracted from read HANDOFF/task file content

## Проблема

Парсер извлекает task ID из **содержимого прочитанных файлов**, а не только из реальных tool calls.

В сессии 84b0f69d работа велась только с `ADV-T030`, но в Tasks попали:
- `T001, T024, T032, T042, T046, T048` — упомянуты в HANDOFF.md и task spec как зависимости/ссылки

## Корневая причина

Тот же паттерн что SA-T069 (tasks-from-task-file-content) и SA-T074 (tasks-from-smoketest-template).
Парсер видит `T001` в тексте Read-результата HANDOFF.md и считает это "работой с задачей".

## Рекомендация

Task extraction должен учитывать только:
1. Реальные tool calls на файлы задач (Read/Edit/Write на `*T0XX*.md`)
2. Явные упоминания в user messages ("сделай T030")
3. TodoWrite items

НЕ из содержимого прочитанных файлов (HANDOFF, specs, architecture docs).

## Ручной фикс сессии 84b0f69d

Tasks исправлены в export: `["ADV-T030"]`.
