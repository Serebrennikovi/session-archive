**Дата:** 2026-04-09
**Статус:** draft
**Severity:** MEDIUM
**Источник:** verify-archive сессии 51cb90a9 (autodev-v2, 2026-04-09)

# SA-T069 — Task IDs извлекаются из контента прочитанного файла задачи, а не из реальной работы

## Проблема

Сессия `51cb90a9` (codereview T028): читался файл `ADV-T028_s04_rate_limit_manager.md`, который содержал многочисленные ссылки на другие задачи в своих секциях (scope, AC, дерево зависимостей). В `session_tasks` попали:

- `T001|implemented` — false positive
- `T024|mentioned` — false positive (T024 упоминается в scope T028)
- `T028|reviewed` — дубликат `ADV-T028`
- `T032|implemented` — false positive (упоминается как T032 BACKLOG в task file)
- `T042|mentioned` — false positive
- `T048|mentioned` — false positive (T048 указан как зависимость T028)

Реально в сессии работали только с T028 (ADV-T028). Все остальные ID — из текста прочитанного задачного файла.

## Как воспроизвести

1. Сессия читает задачный файл T028, который содержит `T024`, `T032`, `T048` в тексте scope/dependencies/AC
2. Парсер находит паттерн `/T\d{3,}/g` во всём контенте Read tool_result
3. В session_tasks добавляются T001, T024, T032, T042, T048 с action `mentioned`/`implemented`
4. T028 добавляется дважды: как `T028` и как `ADV-T028`

## Отличие от смежных багов

- **SA-T063** (tasks-from-artifact-content): тот же класс бага, но прецедент на sproektirui проекте с T042/T099. Данный баг — тот же механизм, другой проект и другие ID. **Возможно, стоит объединить с SA-T063.**
- **SA-T049** (tasks-dedup-and-false-positives): дедупликация T028/ADV-T028 тоже не работает — оба попадают как отдельные записи.

## Root cause

Парсер ищет паттерн `T\d{3,}` в содержимом tool_results (включая Read-результаты) без фильтрации источника. Задачный файл T028 содержит ~10 ссылок на другие задачи в своём тексте.

Дополнительная проблема: `ADV-T028` и `T028` не деduplicируются — обрабатываются как разные task ID.

## Рекомендация по фиксу

1. **Контекстный фильтр:** task ID извлекать только из assistant сообщений (не из tool_result контента Read-вызовов)
2. **Нормализация:** `ADV-T028` → `T028` (strip project prefix), затем дедупликация
3. **Порог evidence:** для `action: implemented` требовать Edit/Write к файлу задачи; для `mentioned` — только если ID упоминается в assistant-тексте, не в прочитанном файле

## Прецедент #2 — сессия 837e25fc (sproektirui, 2026-04-09)

Сессия `/codereview-free T148` + `/fix T148`: реально работали только с **T148**. В `session_tasks` попало `T042|mentioned` — ложный позитив.

Источник: читались файлы HANDOFF.md и ARCHITECTURE.md, которые содержат `T042` в таблицах/истории задач. Парсер извлёк T042 из tool_result содержимого Read-вызовов.

Исправлено вручную: `DELETE FROM session_tasks WHERE session_id='837e25fc...' AND task_id='T042'`.

Паттерн устойчив: баг воспроизводится при чтении любого HANDOFF, который упоминает чужие задачи в таблицах.

## Прецедент #3 — сессия bd314e97 (autodev-v2, 2026-04-09)

Сессия `/codereview-free T045`: реально работали только с **ADV-T045**. В `session_tasks` попали:
- `T001|implemented` — false positive (FIXTURE-T001 из test fixture файлов `tests/fixtures/parity_project/`)
- `T045|reviewed` — дубликат ADV-T045 (без нормализации ADV- prefix)

Источник: сессия читала integration test файлы и fixtures, содержащие FIXTURE-T001. Парсер извлёк `T001` из tool_result.

Исправлено вручную: удалены T001 и T045 из session_tasks.

## Прецедент #4 — сессия ba9d7314 (autodev-v2, 2026-04-13)

Сессия `/codereview t026`: реально работали только с **ADV-T026**. В `session_tasks` попали:
- `T026|reviewed` — дубликат ADV-T026 (без нормализации ADV- prefix)
- `T042|mentioned` — false positive (T042 упоминается в шаблоне skill codereview как пример: "Найди файл задачи: ... T042")
- `T046|reviewed` — false positive (T046 упоминается в task file T026 как зависимость)
- `T099|implemented` — false positive (T099 из шаблона codereview, пример: "номера задач (T099, JIRA-123)")

Новый источник FP: **шаблон skill** (codereview prompt) содержит примеры task ID, которые парсер извлекает как реальные задачи сессии.

Исправлено вручную: удалены T026, T042, T046, T099 из session_tasks.

## Прецедент #5 — сессия bdfaa47b (autodev-v2, 2026-04-14)

Сессия `/intro` + deep codereview T036: реально работали только с **ADV-T036**. В `session_tasks` попали:
- `ADV-T041|reviewed` — false positive (T041 упоминается в HANDOFF.md таблице задач)
- `T029|reviewed` — false positive (T029 в HANDOFF.md)
- `T041|reviewed` — false positive (дубль ADV-T041 без нормализации)
- `T042|mentioned` — false positive (T042 в HANDOFF.md)
- `T046|reviewed` — false positive (T046 в HANDOFF.md)
- `T099|implemented` — false positive (T099 из шаблона codereview skill)

Также затронуты artifacts: 10 файлов помечены как `modified` из git diff (SA-T087), хотя реально менялся только 1 файл.

Исправлено вручную: tasks, artifacts, events, diffs пересобраны.

## Связанные баги

- SA-T063: тот же класс (tasks-from-artifact-content)
- SA-T049: tasks-dedup-and-false-positives
- SA-T066: tasks from archive-skill-template (аналогичный источник — skill template)
- SA-T087: diffs branch-wide, не session-scoped (тот же прецедент bdfaa47b)
