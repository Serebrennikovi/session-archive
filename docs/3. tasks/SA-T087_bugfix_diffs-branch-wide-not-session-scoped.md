**Дата:** 2026-04-14
**Статус:** open
**Severity:** HIGH

# SA-T087: Diffs содержат все изменения ветки, не только правки текущей сессии

## Проблема

Секция `## Diffs` в экспорте содержит полный `git diff main...HEAD` — все изменения ветки, включая коммиты из предыдущих сессий. В результате:
- 10 файлов в artifacts помечены как `modified`, хотя в сессии был отредактирован только 1 файл
- Binary diff `adv` (6MB base64-like) загрязняет экспорт
- Дифф `cmd/adv/main.go` (+140 строк), `internal/artifacts/`, `internal/metrics/`, `internal/plan/state/` — изменения из прошлых сессий, не имеющие отношения к текущей

## Воспроизведение

Сессия `dbb7d694` на ветке `codex/pipeline-hardening-stageb-finalize`:
- В сессии: 3 Edit вызова, все в `ADV-T036_s06_freeze_evaluation.md`
- В diffs: 10 файлов из git diff branch vs main

## Ожидание

Diffs должны содержать только изменения, сделанные в текущей сессии. Варианты:
1. Трекать `git diff HEAD` на момент начала сессии (base_commit) и конца → diff between them
2. Парсить Edit tool calls из JSONL и генерировать synthetic diffs из old_string→new_string
3. Если base_commit пустой (как сейчас `-`) — хотя бы пометить что diffs = branch-wide, а не session-scoped

## Воспроизведение #2

Сессия `bdfaa47b` на ветке `codex/pipeline-hardening-stageb-finalize`:
- В сессии: 2 Edit вызова, все в `ADV-T036_s06_freeze_evaluation.md`
- В diffs: 11 файлов из git diff — `adv` (бинарник), `cmd/adv/main.go`, `ADV-T041`, `ADV-T030`, `artifacts.go`, `artifacts_test.go`, `metrics.go`, `metrics_test.go`, `updater.go`, `evaluator.go`, `freeze_test.go`
- Из 11 только 1 реально менялся в сессии
- Также затронуты artifacts (10 modified → 1 реально modified) и tasks (T041, T029, T042, T046, T099 вместо T036)

## Рекомендация

Приоритет: вариант 1 (base_commit при начале сессии). Если JSONL содержит первое сообщение с timestamp — можно найти ближайший коммит через `git log --before=<timestamp> -1 --format=%H`.
