**Дата:** 2026-04-08
**Статус:** open
**Severity:** HIGH

# SA-T056 — Фантомные artifacts из grep output и каскадные ложные events

## Проблема

Парсер записывает файлы из Grep tool results как artifacts с action=`read`, хотя Grep возвращает только строки с совпадениями, не читает файл целиком. Это создаёт **каскад ложных данных:**

1. **Фантомные artifacts:** файлы из grep output попадают в `session_artifacts` как `read`
2. **Каскадные фантомные events:** `detect_events()` (фикс SA-T004) проверяет artifacts paths → фантомный artifact `S04_spec.md` триггерит `spec_read`, фантомный `ADV-CHANGELOG.md` триггерит `changelog_read`

Фикс SA-T004 заменил text-matching на artifact-based event detection, что корректно. Но предпосылка "artifacts содержат только реальные Read/Edit" нарушена — grep artifacts загрязняют и artifacts, и events.

## Воспроизведение (2026-04-08, session 2c2aa57e)

Сессия: код-ревью ADV-T032 (autodev-v2). Использовались:
- **Read tool:** HANDOFF.md, T032 task file, handoff_sync.go, runner.go, handoff_sync_test.go, config.go, main.go, engine.go
- **Grep tool:** `TaskOutcome` в `internal/pipeline/` → results показали `pipeline.go` и `engine.go`; `NewTaskRun` в `internal/state/` → results показали `state.go` и `state_test.go`; `makeTempScript` в `internal/runner/` → results показали `runner_test.go`

Парсер записал 15 artifacts, из которых 6 ложных:
- `ADV-CHANGELOG.md` (read) — **НЕ читали** (ни Read, ни Grep). Вероятно из git status snapshot ❌
- `executor/executor.go` (read) — **НЕ читали, НЕ grep'али** ❌
- `pipeline/pipeline.go` (read) — из Grep results, не Read ❌
- `state/noop.go` (read) — **НЕ читали, НЕ grep'али** ❌
- `runner/runner_test.go` (read) — из Grep results, не Read ❌
- `S04 spec` (read, via grep) — из Grep results, не Read ❌

Каскадные ложные events:
- `changelog_read` — от фантомного artifact `ADV-CHANGELOG.md` ❌
- `spec_read` — от фантомного artifact `S04 spec` ❌

## Корневая причина

1. **Grep→artifact pipeline:** парсер не различает `Read` (file opened for reading) и `Grep` (pattern search with file paths in results). Оба создают artifacts.
2. **Cascading:** `detect_events()` доверяет artifacts — если artifact path содержит "changelog", event `changelog_read` триггерится. Загрязнённые artifacts → загрязнённые events.
3. **Git status contamination:** некоторые artifacts (executor.go, noop.go) не объяснимы ни Read, ни Grep — вероятно из git status или другого контекстного сканирования.

## Связанные баги

- **SA-T004 (done)** — events detection перешёл на artifact-based → корректен, если artifacts чистые
- **SA-T052 (open)** — diffs/artifacts из git status → аналогичная проблема для modified/deleted файлов
- **SA-T028 (done)** — artifact noise reduction — аналогичная проблема, но для bash mv/rm

## Рекомендация по фиксу

1. **Различать Read vs Grep:** в artifact extraction проверять tool type. `Grep` → не создавать artifact (файл не читался). Или создавать с action=`grepped` (отличимо от `read`).
2. **Event detection:** `detect_events()` учитывать только artifacts с action=`read` (explicit Read tool), не `grepped`.
3. **Git status filtering:** не включать файлы из git status в artifacts, если не было tool call (Read/Edit/Write) для этого файла.
