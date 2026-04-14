**Дата:** 2026-04-09
**Статус:** draft

# SA-T063 — False-positive tasks from artifact/skill content (e.g. T042, T099)

## Проблема

В `session_tasks` попадают task ID из контента прочитанных файлов или системного промпта — не из реальной работы сессии. В сессии `c52bd9af` (visual check T147) появились:
- `T042` — action: `mentioned`
- `T099` — action: `implemented`

Ни T042, ни T099 в сессии не упоминались. Задач с такими номерами в проекте sproektirui в данном контексте не существует (есть SA-T042 в SessionArchive, но это другой проект).

## Как воспроизвести

1. Сессия работает только с T147 (`visualcheck`)
2. Системный промпт или прочитанный файл (`codereview-local.md`, HANDOFF, системные шаблоны) содержит паттерны `T\d+` — например, ссылки на старые задачи
3. `archive-current` / parser находит эти паттерны и записывает их как session tasks

## Root cause (предположение)

Парсер ищет паттерн `/T\d{3,}/g` в контенте JSONL — включая содержимое tool results, system reminders, прочитанных файлов. Он не ограничивается assistant tool calls, обращёнными к задачным файлам.

Частично перекрывается SA-T049 (tasks-dedup-and-false-positives), но в этом случае `action: 'implemented'` для T099 особенно вводит в заблуждение — в задаче ничего не реализовывалось.

## Acceptance Criteria

- [ ] task ID не извлекается из system_reminder блоков, skill templates, tool_results для Read-вызовов не к задачным файлам
- [ ] `action: 'implemented'` не назначается задаче, если не было Write/Edit к файлу этой задачи
- [ ] Сессия с единственной задачей T147 содержит ровно одну запись в session_tasks
