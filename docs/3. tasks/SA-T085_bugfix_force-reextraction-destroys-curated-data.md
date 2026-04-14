**Дата:** 2026-04-12
**Статус:** open
**Severity:** HIGH
**Источник:** verify-archive на сессии `9925b288` (autodev-v2, /fix T034)

# SA-T085 — `--force` re-extraction уничтожает curated данные и заменяет на мусор

## Проблема

Когда сессия имеет `manually_reviewed=1`, повторный `archive-current` выводит:
```
Warning: session 9925b288 is manually reviewed. Updating counts only.
```
Это корректная защита (SA-T036). Но если пользователь запускает `--force` для обновления архива (например, после дополнительной работы в той же сессии), re-extraction:

1. **Уничтожает** вручную выверенный summary, tasks, events, artifacts, diffs
2. **Заменяет** на auto-extracted данные, которые содержат ВСЕ известные баги:
   - Tasks: T042, T045 вместо T034 (SA-T069 — false positives из контента файлов)
   - Diffs: ВСЕ uncommitted файлы из git, не только session-specific (SA-T075)
   - Tool calls: 0 (SA-T079)
   - Events: только `session_archived` (SA-T059/SA-T083)
   - Artifacts: все uncommitted файлы помечены как `modified` (SA-T084)
   - Skills: `intro` вместо `intro, fix` (SA-T082)

Результат: `--force` — escape hatch, который делает хуже, а не лучше.

## Воспроизведение

1. Архивировать сессию: `archive-current --summary "correct summary"`
2. Запустить `/verify-archive` → исправить ошибки → `manually_reviewed=1`
3. Продолжить работу в той же сессии (новые tool calls, новые edits)
4. Запустить `archive-current --force --summary "updated summary"`
5. Проверить: curated artifacts/diffs/tasks/events заменены на auto-extracted мусор

## Root cause

`--force` вызывает полную re-extraction, которая использует те же broken extractor functions:
- `extract_tasks()` — парсит контент file reads (SA-T069)
- `build_diffs()` — берёт `git diff HEAD` для всего (SA-T075)
- `count_tool_calls()` — не работает с `--tool-ids` (SA-T079)
- `extract_events()` — почти ничего не детектит (SA-T059)
- `extract_artifacts()` — помечает read-only файлы как modified (SA-T084)

## Рекомендация

**Вариант A (минимальный):** При `--force` с `manually_reviewed=1` — НЕ перезаписывать поля, которые были вручную выверены (summary, tasks, events, skills, artifacts). Обновлять ТОЛЬКО: msg_count, tool_call_count, и ДОБАВЛЯТЬ новые diffs (session-specific, не всех uncommitted).

**Вариант B (правильный):** Починить все underlying extraction bugs (SA-T069, SA-T075, SA-T079, SA-T059, SA-T084) — тогда `--force` будет давать корректные данные.

**Вариант C (промежуточный):** `--force` с `manually_reviewed=1` → merge-стратегия: оставить curated fields, добавить новые данные (новые diffs, обновить counts).

## Связанные баги

- SA-T036 (защита manually_reviewed — работает, но --force обходит её by design)
- SA-T069 (tasks false positives из контента)
- SA-T072 (rerun overwrites before review)
- SA-T075 (diffs from uncommitted prior sessions)
- SA-T079 (tool_calls = 0)
- SA-T084 (cross-session contamination from git uncommitted)
