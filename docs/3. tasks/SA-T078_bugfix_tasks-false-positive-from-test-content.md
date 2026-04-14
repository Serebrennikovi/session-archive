# SA-T078 — Tasks false positive from test content in diffs/artifacts

**Дата:** 2026-04-12
**Severity:** LOW
**Обнаружено:** verify-archive сессия `fa809fcb` (AutoDev v2, 2026-04-11)

## Описание

Task extractor может ошибочно извлечь task ID из содержимого тестовых данных или diff-контента. Пример: строка `#### Issue 42: forged` в тестовом fixture для findings parser создала false-positive `T042` в списке задач (позже исправлено скриптом на `ADV-T034`, но первичная экстракция была неверной).

## Механизм

Diff artifacts содержат строки вида:
```
"### CRITICAL\n#### Issue 1: x\n- body\n\n## Round 99\n### HIGH\n#### Issue 42: forged\n- body\n"
```

Task extractor видит `42` и матчит его как `T042`.

## Ожидаемое поведение

Task IDs должны извлекаться только из:
- Явных упоминаний в формате `T\d+` / `ADV-T\d+` в тексте conversation (не в code/diffs)
- Tool call arguments содержащих task IDs
- File paths содержащих task IDs

Содержимое diff hunks, строковых литералов в коде, и test fixtures не должно учитываться.

## Связь с другими багами

- **SA-T074** (tasks false positive from smoketest template) — тот же класс: контент из шаблонов/тестов загрязняет task list.
- **SA-T069** (tasks false positive from task file content) — аналогичный: контент внутри файлов задач создаёт phantom tasks.
