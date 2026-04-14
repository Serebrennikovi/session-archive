**Дата:** 2026-04-07
**Статус:** open
**Severity:** MEDIUM

# SA-T051 — Tasks section пустая при вызове через /next skill

## Проблема

Когда сессия запускается через skill `/next`, парсер не извлекает task IDs совсем. Результат — пустая секция `## Tasks` в export, несмотря на то что сессия целиком посвящена одной задаче (ADV-T024).

### Воспроизведение (2026-04-07, session 791a400c)

1. Пользователь вызвал `/next`
2. Скилл развернулся в промпт, который прочитал HANDOFF и выбрал ADV-T024
3. Вся сессия — реализация ADV-T024 (создание `internal/executor/`, 25 тестов, lint fixes)
4. `archive-current` → Tasks: пусто

### Вероятная причина

Парсер ищет task IDs в user messages или assistant text, но:
- Task ID `T024` / `ADV-T024` фигурирует в assistant responses и tool results, а не в user message text
- User messages содержат только `<command-message>next</command-message>` и summary для archive
- Парсер может не сканировать assistant text или tool_result content для task extraction

### Связь с SA-T049

SA-T049 описывает проблему **false positives** (слишком много задач). Этот баг — **false negatives** (задачи не найдены). Фикс должен быть согласован: нужен баланс между избыточным извлечением и полным пропуском.

### Воспроизведение 2 (2026-04-13, session 946bb737, sales)

1. Пользователь вызвал `/next` с аргументом `arb website`
2. Скилл прочитал HANDOFF, выбрал ARB-T03
3. Вся сессия — реализация ARB-T03 (index_v3.html, modal form, theme toggle, Platokhin audit)
4. `archive-current` → Tasks: пусто
5. Ручной фикс: добавлена строка `ARB-T03` в export .md

## Рекомендация по фиксу

1. **Сканировать assistant text** на task ID patterns (T\d{3,4}, ADV-T\d{3,4})
2. **Приоритетный источник**: TodoWrite tool calls — если assistant использует TodoWrite с task-related content, извлекать task ID оттуда
3. **Второй источник**: файлы задач в tool_use Read/Edit calls (паттерн `tasks/.*ADV-T\d+` в file_path)
4. **Fallback**: assistant text mentions — но только если task ID повторяется ≥3 раз
