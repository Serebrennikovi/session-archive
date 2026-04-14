**Дата:** 2026-04-14
**Статус:** draft
**Severity:** HIGH
**Воспроизведение:** session 84b0f69d (autodev-v2, 2026-04-14)

# SA-T090: Diffs & artifacts include all branch uncommitted changes, not session-scoped

## Проблема

Export содержит diffs и artifacts для **8 файлов, которые не были затронуты в этой сессии**:
- `adv` (binary) — prior session build artifact
- `cmd/adv/main.go` — prior session changes
- `ADV-T036_s06_freeze_evaluation.md` — prior session
- `ADV-T041_s08_...md` — prior session
- `internal/plan/findings/updater.go` — prior session
- `internal/plan/freeze/evaluator.go` — prior session
- `internal/plan/freeze/freeze_test.go` — prior session
- `internal/plan/state/store_test.go` — prior session

Единственный реально изменённый файл: `ADV-T030_s05_artifact_compat.md` (Edit tool call).

## Корневая причина

`git_head` diff strategy (`git diff HEAD`) captures **all uncommitted changes on the branch**, regardless of session boundary. When a user works across multiple sessions without committing between them, each new session's archive picks up diffs from all prior sessions.

Тот же паттерн что SA-T075 / SA-T084 / SA-T087.

## Рекомендация

**Session-scoped diff strategy:**
1. При наличии `tool_ids` — diff только файлы, которые были в Write/Edit tool calls этой сессии
2. Fallback: `git stash` snapshot at session start vs current working tree
3. Или: diff `git diff HEAD` filtered by files touched by session tool calls

Также: binary файлы (`adv`) вообще не должны попадать в diffs — добавить фильтр по расширению или `git diff --stat` check.

**Артефакты** из git_head diffs тоже не должны попадать в Artifacts секцию как "modified" — они не были modified в этой сессии.

## Ручной фикс сессии 84b0f69d

- Artifacts: удалены 8 phantom entries + `/tmp/smoketest_t030`
- Diffs: удалены 8 phantom diff sections (1167 строк), оставлен только T030 task file diff
