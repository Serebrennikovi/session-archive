**Дата:** 2026-04-08
**Статус:** draft
**Источник:** verify-archive сессии 6210a39a

# SA-T059 — Неполное определение events

## Баг

Парсер не детектирует `code_reviewed` и `lint_run` events, хотя они реально произошли в сессии.

**Воспроизведение:** сессия 6210a39a:
- Вызван `/codereview` (Skill tool) → `code_reviewed` **не детектирован**
- Запущены `go vet ./...`, `go build ./...` через Bash → `lint_run` **не детектирован**
- `tests_run` ✅ детектирован (через `go test`)

**Причина:** event detection, вероятно, ищет конкретные паттерны (`go test` → `tests_run`), но не ищет:
- Skill tool invocations с `skill: "codereview"` → `code_reviewed`
- Bash calls содержащие `go vet`, `eslint`, `ruff` → `lint_run`

**Impact:** history of code review activity incomplete.

## Рекомендация

1. Добавить detection: Skill tool call с `skill: "codereview"` → event `code_reviewed`
2. Добавить detection: Bash call содержащий `vet`, `lint`, `eslint`, `ruff`, `pylint` → event `lint_run`

## Прецедент #2 — сессия a1d889f9 (autodev-v2, 2026-04-11): ложный `handoff_read`

Обратный случай — **ложный позитив** вместо false negative.

Сессия `/codereview t052` не читала `docs/ADV-HANDOFF.md` (скилл `/codereview` идёт напрямую к task-файлу по номеру, минуя HANDOFF). Но в events записан `handoff_read`. В `session_artifacts` HANDOFF.md отсутствует — т.е. файл действительно не был прочитан через Read tool.

**Предположение о триггере:** детектор ищет слово `HANDOFF` в тексте разговора. Шаблон `/codereview` в шаге 1 содержит текст *"HANDOFF — найди строку `**Выполнено (...)**`"* и *"найди в HANDOFF"*. Этого совпадения достаточно, чтобы парсер добавил event `handoff_read`, хотя файл ни разу не открывался.

**Исправлено вручную:** `handoff_read` удалён из SQLite session_events и export .md.

**Рекомендация:** event `handoff_read` детектировать **только** из session_artifacts: если путь содержит `HANDOFF` и action ∈ {read, modified}, то писать event; иначе — нет. Текстовые упоминания в prompt-шаблонах игнорировать.

## Прецедент #3 — сессия de196494 (sales, 2026-04-13): пропущены screenshot, web_research, memory_saved, task_created

Сессия реально выполнила:
- 2 скриншота через Playwright MCP (`browser_take_screenshot`) → event `screenshot_taken` **не детектирован**
- 3 web search через Agent subagents (Жигалов, Газпромбанк VP, CV) → event `web_research` **не детектирован**
- 2 memory файла созданы (Write tool) → event `memory_saved` **не детектирован**
- 1 task создана (ARB-T03, Write tool) → event `task_created` **не детектирован**

**Причина:** парсер не имеет правил для MCP tool calls (`mcp__playwright__*`), Agent tool subagent results, и Write tool calls к memory-файлам.

**Рекомендация:**
1. `screenshot_taken` ← MCP tool call `mcp__playwright__browser_take_screenshot`
2. `web_research` ← Agent tool call где prompt содержит "web search" / "поиск" / WebSearch
3. `memory_saved` ← Write tool call к путям содержащим `/memory/`
4. `task_created` ← Write tool call к путям содержащим `/tasks/` и action = created

## Прецедент #4 — сессия 5cf74de4 (autodev-v2, 2026-04-13): ложные `handoff_read` + `spec_read`

Сессия `/codereview-free t029`. Парсер записал `handoff_read` и `spec_read`, хотя ни HANDOFF.md, ни spec S05 не читались через Read tool. Реальные Read-вызовы: task file T029, 10+ Go-файлов. HANDOFF и spec фигурируют только в тексте assistant messages (упоминания в code review findings) и в gitStatus контексте.

Паттерн идентичен прецеденту #2 — event detection триггерится на текстовые упоминания "HANDOFF" / "spec" в assistant output, а не на фактические Read tool calls.

**Исправлено вручную:** events заменены на `code_read, tests_run, memory_written, session_archived`.
