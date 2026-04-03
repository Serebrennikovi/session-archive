**Дата:** 2026-04-03
**Статус:** done
**Завершено:** 2026-04-03
**Спецификация:** —

# SA-T036 — Исправить: повторный archive-current уничтожает ручные правки + регрессии action/event

## Customer-facing инкремент

Повторный запуск `archive-current` для уже заархивированной сессии не уничтожит вручную исправленные теги, задачи и события. Write tool на существующий файл снова будет корректно записываться как `modified`, а не `created`. `event:tests` pseudo-entries больше не будут появляться в артефактах.

---

## Баги

### BUG-RERUN-OVERWRITE — archive-current перезаписывает все ручные правки

**Симптом:** При повторном запуске `archive-current --model claude-sonnet-4-6` на сессию, которая уже была заархивирована и вручную исправлена:
- `session_tags` полностью удаляются и пересоздаются из JSONL (ручные правки тегов теряются)
- `session_tasks` полностью удаляются и пересоздаются (ручные правки задач теряются)
- `session_events` полностью удаляются и пересоздаются (ручные правки событий теряются)
- `sessions.summary` может быть перезаписан если не был передан `--summary`

Из сессии `aa723310`: "Явно переданный `--summary` при первом вызове теряется. Рекомендация: при повторном `archive-current` с тем же session_id — обновлять только msg_count и tool_call_count, НЕ перезаписывать summary если он уже был задан вручную."

**Повторялось:** 1+ раз явно, вероятно происходит регулярно (в SA-T030 есть родственный BUG-ARCHIVE-OVERWRITE regression).

**Root cause:** `archive-current` при обнаружении существующего `session_id` делает `DELETE FROM session_tags WHERE session_id=?` + полный re-insert, аналогично для tasks и events. Нет различия между "первый запуск" и "повторный запуск после ручных правок".

**Fix (реализовано):**

Добавлено поле `manually_reviewed` (INTEGER DEFAULT 0) в таблицу `sessions`. При повторном `archive-current`:
- Если `manually_reviewed = 1` и нет `--force` флага → выводит предупреждение, обновляет только `msg_count`, `tool_call_count`, `ai_model` — теги/задачи/события не трогаются
- `--force` флаг добавлен в `parse_archive_current_args` и передаётся в `write_session(force=True)` для принудительной перезаписи

---

### BUG-ARTIFACT-ACTION-WRONG — Write на существующий файл → action=created (регрессия)

**Fix (реализовано):** В `extract_artifacts` для Write tool добавлена проверка `git ls-files --error-unmatch <path>` если файл не был в `seen_read`. Если файл tracked в git → `action='modified'`.

---

### BUG-ARTIFACT-EVENT-PSEUDO — `event:tests` entries в session_artifacts (регрессия)

**Fix (реализовано):** В `_init_schema` добавлена одноразовая очистка дублирующихся `event:*` записей из `session_artifacts` при создании уникального индекса. Индекс `idx_session_artifacts_unique` теперь создаётся только после очистки данных, предотвращая ошибку IntegrityError при миграции.

---

## Scope

- ✅ Добавить `manually_reviewed` флаг в `sessions` и защиту при повторном archive-current
- ✅ Исправить регрессию BUG-ARTIFACT-ACTION-WRONG (Write → created/modified классификация через git ls-files)
- ✅ Исправить регрессию BUG-ARTIFACT-EVENT-PSEUDO (очистка + уникальный индекс в `_init_schema`)

## Out of scope

- Автоматическое определение manually_reviewed из истории (только явная установка)
- Изменение поведения при `--force` флаге

---

## Как протестировать

1. Заархивировать сессию → вручную исправить теги → повторно запустить `archive-current` → теги должны остаться (предупреждение в stdout)
2. Сессия с Write на существующий файл (без предварительного Read) → action=modified если файл в git
3. Сессия с `make test` или `npm test` в Bash → `event:tests` в artifacts не должны появляться

## Критерии приёмки

1. ✅ Повторный `archive-current` без `--force` не перезаписывает вручную исправленные данные
2. ✅ Write на tracked git файл → `action=modified`, не `created`
3. ✅ `session_artifacts` не содержит записей с `file_path` начинающимся на `event:`
