**Дата:** 2026-04-14
**Статус:** open
**Severity:** MEDIUM

# SA-T088: Events не детектируются из tool calls (code_review, tests_run)

## Проблема

Скрипт записал только 1 event (`session_archived`), хотя в сессии были:
- `code_review_run` — 4 параллельных Agent вызова для code review
- `tests_run` — `go test -race -count=1` через Bash tool
- `severity_correction` — пользователь попросил скорректировать оценки, были Edit вызовы

## Воспроизведение

Сессия `dbb7d694`:
- 4x Agent tool calls с описаниями содержащими "codereview", "smoketest", "edge-case", "codereview-free"
- Bash tool call с `go test -race`
- Записано events: только `session_archived`

## Ожидание

Events должны детектироваться из:
1. Agent tool descriptions содержащих keywords (review, test, smoke)
2. Bash commands содержащих `go test`, `npm test`, `pytest` etc.
3. Skill invocations (`/codereview`, `/smoketest`)

## Рекомендация

Расширить event detection rules:
- Agent description matches `review|codereview` → `code_review_run`
- Agent description matches `test|smoke` → `tests_run`
- Bash command matches `go test|npm test|pytest` → `tests_run`
- Skill name matches `codereview|smoketest` → соответствующий event

Связано с: SA-T083 (events-code-reviewed-not-detected) — возможно дублирует, проверить scope.
