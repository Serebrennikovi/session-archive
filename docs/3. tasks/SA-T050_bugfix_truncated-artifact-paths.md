**Дата:** 2026-04-07
**Статус:** open
**Severity:** LOW

# SA-T050 — Обрезанные пути артефактов с пробелами

## Проблема

Артефакт `/Users/is/.../docs/5. Unsorted/ADV-S04-S08_hardening_review_findings.md` записан как `docs/5.` (deleted). Парсер обрезает путь на первом пробеле после точки.

## Воспроизведение

1. Удалить файл с путём содержащим пробел (например `docs/5. Unsorted/file.md`)
2. Архивировать
3. В артефактах: путь обрезан до `docs/5.`

## Новое воспроизведение (2026-04-07, session e892faa8)

Файл перемещён через `mv "docs/3. tasks/.../ADV-T023_s04_sqlite_task_runtime.md" "docs/3. tasks/Done/..."`.
Результат в артефактах:
- `moved_from`: `/Users/is/.../docs/3.` (обрезано на пробеле после `3.`)
- `moved_to`: `tasks/ADV-S04_.../ADV-T023_...md` (потерян prefix, не абсолютный путь)

Root cause тот же: парсер Bash mv-команд разбивает путь по пробелам.

### Новое воспроизведение (2026-04-09, session 947a5082)

`mv "docs/3. tasks/ADV-S05_.../ADV-T049...md" "docs/3. tasks/Done/ADV-S05..._done/ADV-T049..._done.md"` во время `/accept`.

Результат в SQLite session_artifacts:
- id=7090 `moved_from`: `/Users/is/personal/Projects/09_AutoDev_v2/docs/3.` (обрезано на пробеле)
- id=7091 `moved_to`: `tasks/ADV-S05_go_intra_project_orchestration/ADV-T049_s05_structured_markdown_parser.md` (потерян `/Users/is/.../docs/3. ` prefix и суффикс `_done`)

Дополнительно: `id=7083` помечен как `deleted` (от git diff), хотя это тот же файл что moved_from. Результат — дублирующие записи (один файл фигурирует и как `deleted` и как `moved_from`). Вручную исправлено: удалён id=7090, id=7083 переведён в `moved_from`, id=7091 обновлён до полного Done-пути.

## Рекомендация по фиксу

Использовать regex-паттерн для извлечения пути который учитывает кавычки и стандартные расширения (.md, .go, .py, .sh). Или парсить tool_use input напрямую (path всегда в JSON-поле `file_path`). Для Bash mv/cp команд — парсить аргументы с учётом кавычек (`"path with spaces"`).
