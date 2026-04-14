**Дата:** 2026-04-12
**Статус:** open
**Sev:** MEDIUM

# SA-T079 — Tool calls count всегда 0

## Проблема

В метаданных экспорта `| Tool calls | 0 |` даже когда сессия содержит 18+ tool calls (Glob, Read, Bash, Edit, Write).

## Воспроизведение

Сессия `a8e931c1` (autodev-v2, 2026-04-12): реально 18+ tool calls (Glob ×3, Read ×12, Bash ×3, Edit ×2, Write ×2), в экспорте `Tool calls | 0`.

## Root cause

Вероятно парсер не считает tool calls при наличии `--tool-ids` фильтрации, либо `tool_calls` поле заполняется отдельной веткой кода, которая не задействуется.

### Воспроизведение 2 (2026-04-12, session `69d11152`)

Сессия autodev-v2, codereview T046: реально ~17 tool calls (Agent, Read ×8, Grep ×3, Bash ×4, Edit ×1), в экспорте `Tool calls | 0`. Исправлено вручную при verify-archive.

### Воспроизведение 3 (2026-04-13, session `410df60f`)

Сессия autodev-v2, skill updates: реально ~22 tool calls (Glob ×4, Read ×12, Edit ×6, Bash ×3, Skill ×1, TodoWrite ×3), в экспорте `Tool calls | 0`. Исправлено вручную при verify-archive.

### Воспроизведение 4 (2026-04-14, session `c1332233`)

Сессия autodev-v2, fix T029: реально ~40+ tool calls (Glob ×4, Read ×15, Edit ×20, Bash ×8, Skill ×2, TodoWrite ×5), в экспорте `Tool calls | 13`, `Messages | 2`. Обе цифры сильно занижены. Исправлено вручную при verify-archive.

### Воспроизведение 5 (2026-04-14, session `21dee077`)

Сессия autodev-v2, codereview T036: реально ~25 tool calls (Agent ×1, Read ×12, Grep ×6, Bash ×4, Edit ×1, Skill ×1), в экспорте `Tool calls | 4`. Исправлено вручную при verify-archive.

## Рекомендация

Проверить `extract_metadata()` или аналогичную функцию — посчитать количество tool_use блоков в отфильтрованных messages.
