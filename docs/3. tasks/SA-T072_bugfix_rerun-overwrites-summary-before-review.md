**Дата:** 2026-04-09
**Статус:** open
**Severity:** HIGH

# SA-T072 — Повторный archive-current перезаписывает summary до manually_reviewed

## Проблема

SA-T036 добавил защиту `manually_reviewed=1` от перезаписи ручных правок при rerun. Но между первым `archive-current --summary "..."` и установкой `manually_reviewed=1` (которую делает verify-archive) — есть окно, в котором:

1. JSONL файл продолжает расти (verify-archive делает tool calls → новые сообщения в JSONL)
2. Любой повторный вызов `archive-current` перезаписывает всё (manually_reviewed ещё 0)
3. Парсер генерирует summary из JSONL-контента, который может содержать данные предыдущих сессий

## Воспроизведение — session fb6419f7 (sproektirui, 2026-04-09)

1. `archive-current --summary "Код-ревью T149..."` → summary корректен
2. Сразу после — запущен `/verify-archive` → tool calls добавили 3+ сообщения в JSONL
3. К моменту чтения export .md (Read tool в verify-archive) — файл уже содержал:
   - `summary: Код-ревью задачи T148...` (от **предыдущей** сессии в этом же JSONL!)
   - `Messages: 21` (вместо 18)
   - `Tool calls: 0` (счётчик сброшен)
4. `manually_reviewed` был 0 → защита SA-T036 не сработала

**Каскадный эффект:** перезаписанный summary T148 содержал информацию о чужой задаче, создавая ложное впечатление о работе сессии.

## Root cause

JSONL файл Claude Code = вся сессия IDE (может содержать несколько "разговоров"). Парсер не различает границу между conversations внутри одного JSONL. При повторном парсе он берёт summary/tasks/tags из ВСЕГО файла, а не из конкретного conversation.

Плюс: `manually_reviewed` guard из SA-T036 работает только после явной установки (verify-archive). Между первым archive и verify — данные не защищены.

## Рекомендация по фиксу

**Опция A (быстрая):** `archive-current --summary "..."` при первом запуске должен устанавливать `summary_manual` как приоритетный и НЕ перезаписывать его при rerun, даже если `manually_reviewed=0`. Правило: если `summary_manual IS NOT NULL` → не трогать при rerun.

**Опция B (надёжная):** При первом archive-current сразу устанавливать `manually_reviewed=1` если передан `--summary`. Логика: пользователь уже вручную контролирует данные → защитить от автоматической перезаписи.

**Опция C (defensive):** Никогда не делать rerun автоматически. Если JSONL изменился после archive — предупреждать, но не перезаписывать.

## Воспроизведение #2 (2026-04-09, session f8a14e62)

1. Предыдущая сессия (T151) вызвала `archive-current --summary "T151..."` → `summary_manual` заполнен
2. Текущая сессия (T153) вызвала `archive-current --summary "T153..."` → `summary_manual` НЕ обновлён (содержит T151 текст)
3. `--summary` CLI аргумент был проигнорирован — скрипт видит `summary_manual IS NOT NULL` и не перезаписывает
4. **Вывод:** при rerun на том же session_id, `--summary` должен ВСЕГДА побеждать существующий `summary_manual`. CLI аргумент = явное намерение пользователя.

## Воспроизведение #3 (2026-04-13, session 2ab24fa4, sproektirui)

1. Предыдущая сессия архивировала в тот же JSONL с summary "перенесли 4 карточки... cache-bust..."
2. Текущая сессия вызвала `archive-current --summary "Сортировка карточек Trello... T149... T153..."` — явный `--summary` передан
3. Export содержит summary от **предыдущей** сессии, а не переданный через `--summary`
4. `manually_reviewed` = 0 → защита SA-T036 не сработала
5. Парсер вероятно сгенерировал summary из JSONL-контента (содержащего messages предыдущей сессии) и перезаписал `--summary`

**Вывод:** `--summary` CLI аргумент должен ВСЕГДА иметь приоритет над парсером, вне зависимости от `manually_reviewed` и `summary_manual`.

## Связанные баги

- SA-T036 (done) — rerun overwrite regressions (исходный фикс, недостаточный)
- SA-T052 (open) — phantom diffs/artifacts из git status (каскадный эффект)
- SA-T073 (open) — cross-session contamination (корневая причина)
