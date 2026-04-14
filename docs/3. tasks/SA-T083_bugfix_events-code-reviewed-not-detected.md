**Дата:** 2026-04-12
**Статус:** open
**Sev:** MEDIUM

# SA-T083 — Event `code_reviewed` не детектируется при code review сессиях

## Проблема

Сессия, целиком посвящённая code review (skill `codereview-free`, Edit записывает findings в task file), не получает event `code_reviewed`. Единственный event — `session_archived` (meta-action).

## Воспроизведение

Сессия `31408eb9` (autodev-v2, 2026-04-12):
- Skill: `codereview-free`
- Edit: task file с CR findings (секции "Code Review", "Находки", "Verdict")
- Events (парсер): `session_archived` only
- Events (ожидается): `code_reviewed`, `task_file_updated`, `session_archived`

## Root cause

Связан с SA-T059 (events incomplete detection). `detect_events()` не имеет правила для `code_reviewed`:
- Нет детекции по skill name (`codereview*` → `code_reviewed`)
- Нет детекции по контенту Edit (секция "## Code Review" добавлена в .md файл)
- `task_file_updated` тоже не детектируется (Edit вызов на файл `docs/3. tasks/.../*.md`)

### Воспроизведение 2 (2026-04-12, session `4e419074`)

Сессия: review T057 задачи (не через skill `codereview*`, а прямой ручной review по просьбе пользователя). Ассистент написал полный review с таблицей findings, severity, рекомендациями. Парсер не обнаружил `code_reviewed`.

**Дополнительный паттерн:** code review может происходить не только через `/codereview*` skill, но и напрямую — пользователь просит «придирчиво отревью» и ассистент выдаёт structured review. В этом случае skill-based inference не поможет.

**Дополнительная рекомендация:** детектировать `code_reviewed` по content patterns в assistant messages:
- Наличие structured table с колонками `Severity`/`Проблема`/`Рекомендация`
- Секции типа «## Ревью», «## Review», «## Итого: найденные проблемы»
- Паттерн «CRITICAL/HIGH/MEDIUM/LOW» severity classification

### Воспроизведение 3 (2026-04-12, session `898fa735`)

Сессия: третье независимое код-ревью T057. Skill `codereview-free` вызван + ручной review с `go build/test/vet` + Edit task file с полной секцией "Code Review — 2026-04-12 21:30". Парсер обнаружил `tests_run` (через Bash `go test`), но `code_reviewed` пропущен. Подтверждает паттерн из воспроизведений 1-2.

### Воспроизведение 4 (2026-04-13, session `ba9d7314`)

Сессия: `/codereview t026` на autodev-v2 (Go scheduler code review). Skill `codereview` вызван, 11 findings записаны через Edit в task file. Парсер обнаружил `spec_read`, `tests_run`, `session_archived`, но НЕ `code_reviewed`. Подтверждает все предыдущие воспроизведения.

### Воспроизведение 5 (2026-04-14, session `21dee077`)

Сессия: `/codereview-free T036` + `/fix` на autodev-v2. Skill `codereview-free` вызван, Code Review #2 написан с structured findings table через Edit в task file. Также `go test -race` run (→ `tests_run` ✅). Парсер обнаружил `tests_run` и `session_archived`, но НЕ `code_reviewed`. Вручную добавлен через SQLite INSERT.

## Рекомендация

1. **Skill-based event inference**: если `skill: codereview*` → добавить event `code_reviewed`
2. **Edit-based event inference**: если Edit path содержит `docs/3. tasks/` → добавить event `task_file_updated`
3. Рассмотреть general mapping: skill → implied events (codereview → code_reviewed, smoketest → tests_run, fix → code_fixed, accept → task_accepted)
