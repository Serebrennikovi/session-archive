**Дата:** 2026-04-03
**Статус:** done
**Завершено:** 2026-04-03
**Спецификация:** —

# SA-T019 — Исправить pseudo-artifacts event:* в session_artifacts

## Customer-facing инкремент

После архивирования сессии `## Artifacts` будет содержать только реальные файлы — без строк `event:tests`, `event:deploy`, `event:commit`. Shell-read файлы (прочитанные через `sed`, `cat`, `rg`, `sqlite3`) будут корректно попадать в артефакты.

---

## Баги

### BUG-22 — session_artifacts смешивает pseudo-events с файлами

**Симптом:** В `session_artifacts` и секции `## Artifacts` появляются строки вида `event:deploy`, `event:tests` — как будто это файловые пути. При этом реальные файлы, прочитанные через shell-команды (`sed`, `cat`, `diff`, `git diff -- <path>`), в артефакты не попадают.

**Root cause:** Event extraction и artifact extraction используют один пайплайн. Event-эвристика протекает в `session_artifacts` как fake path `event:*`. Чтения через `exec_command` не парсятся как `read`-артефакты.

**Повторялось:** 6+ раз, каждый раз исправляется вручную.

**Fix:**
- Никогда не записывать `event:*` в `session_artifacts`; события должны жить только в `session_events`.
- Разделить пайплайны event extraction и artifact extraction: event-эвристики не могут создавать pseudo-file path.
- Добавить фильтр: если `file_path.startswith('event:')` → пропустить при записи в `session_artifacts`.

---

### BUG-24 — pseudo-artifacts event:tests повторяют BUG-22 для тестовых событий

**Симптом:** В `session_artifacts` появляются 1–4 записи `event:tests`, хотя тесты — это событие, а не файл. Одновременно теряются реальные shell-read файлы: `HANDOFF.md`, `run.sh`, skill docs, test scripts — всё что читалось через `sed`/`rg`/`tail` в ходе review.

**Root cause:** Та же причина что BUG-22, но для `tests_run` event. Дополнительно: `exec_command` читает файлы через shell, и эти reads не парсятся как artifact evidence.

**Повторялось:** 7+ раз, каждый раз исправляется вручную.

**Fix:**
- Парсить явные file-read паттерны в `exec_command`: `sed -n 'N,Mp' <path>`, `cat <path>`, `head -N <path>`, `tail -N <path>`, `nl <path>`, `diff <path>`, `git diff -- <path>`, `sqlite3 <db> "SELECT ..."`.
- Для каждого найденного пути добавлять в `session_artifacts` с `action=read`.
- Добавить regression-test: сессия с `tests_run` event и shell-read `run.sh`/`test_*.sh` → `session_events=['tests_run']`, artifacts — file list без `event:tests`.

---

### BUG-41 — Intro + fix сессии архивируются с чужими задачами и event:* артефактами

**Симптом:** После `session-archive` для сессии с `intro` + `fix` + `archive`: `session_artifacts` содержит `event:commit`, `event:push`, `event:tests`; реальные файлы (skill docs, HANDOFF, architecture, test scripts, run.sh) потеряны. `session_tasks` содержит чужие task IDs из прочитанных docs.

**Root cause:** Комбинация BUG-22/BUG-24 (event pseudo-artifacts) + BUG-TASKS-FROM-CONTEXT (task IDs из прочитанных файлов). Artifact extractor работает из единого нефильтрованного потока.

**Повторялось:** 5+ раз, каждый раз исправляется вручную.

**Fix:**
- Применить фиксы из BUG-22 и BUG-24 (фильтр event:* + shell-read парсинг).
- Дополнительно: не добавлять `event:*` как artifact даже если event detection был ранее в том же pipeline run.

---

## Scope

- Удалить все пути вида `event:*` из записи в `session_artifacts`
- Добавить парсинг shell-read операций в `exec_command` как `action=read` артефакты
- Разделить event extraction pipeline и artifact extraction pipeline

## Out of scope

- Изменение структуры `session_events` (только артефакты)
- Парсинг сетевых запросов, команд без file-аргументов

---

## Как протестировать

1. Запустить `archive-current` на сессии где были `tests_run` + shell `sed`/`cat` reads
2. Проверить `session_artifacts` — нет записей с `file_path LIKE 'event:%'`
3. Проверить что `session_events` содержит `tests_run` (событие не потеряно)
4. Прочитанные через `sed`/`cat` файлы присутствуют в artifacts с `action=read`

## Критерии приёмки

1. `session_artifacts` не содержит ни одной записи с `file_path` начинающимся на `event:`
2. Shell-read файлы (`sed -n 'N,Mp' path`) появляются в артефактах с `action=read`
3. `session_events` сохраняет все события (deploy, tests_run и др.)
