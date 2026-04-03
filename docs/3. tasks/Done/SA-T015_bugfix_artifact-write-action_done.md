**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T015 — Исправить artifact action: Write на tracked файле = "created" вместо "modified"

## Customer-facing инкремент

После архивирования tracked файлы (те что уже в git), перезаписанные через Write tool, получают action=`modified`, а не `created`. История артефактов корректно отражает реальный тип изменения.

---

## Баги

### BUG-ARTIFACTS-WRITE-ACTION — Write tool на существующем файле классифицируется как "created"

**Симптом:** `session_artifacts` содержит `action="created"` для файла, который реально существовал в репозитории до сессии и был перезаписан через Write tool. Правильный action — `"modified"`.

**Пример из сессии 54332c00 (2026-04-03):** `internal/state/state.go` был `M` (modified) в git status, т.е. существовал ещё до нашей работы. Однако мы его полностью перезаписали через Write tool. Архив записал `action="created"`.

**Root cause:** `classify_artifact_action()` (или аналогичная функция) определяет action по типу tool call:
- `Write` → `created`
- `Edit` → `modified`

Но это неверно: Write может перезаписывать существующий файл. Нужно проверять контекст:
1. Был ли файл прочитан через Read tool до Write? → `modified`
2. Есть ли файл в git diff `--name-status` с статусом `M`? → `modified`
3. Файл был только что создан (не читался, не в git) → `created`

**Повторялось:** неизвестно (обнаружен 2026-04-03), вероятно существовал с самого начала.

**Fix:**

```python
def classify_write_action(file_path: str, prior_reads: set[str], git_modified: set[str]) -> str:
    """
    Classify Write tool action as 'created' or 'modified'.

    - If file was Read before Write → modified
    - If file appears in git diff --name-status as M → modified
    - Otherwise → created
    """
    if file_path in prior_reads:
        return 'modified'
    if file_path in git_modified:
        return 'modified'
    return 'created'
```

Где `prior_reads` — множество путей файлов, прочитанных Read tool ранее в той же сессии.
`git_modified` — вывод `git diff HEAD --name-status` (relative to project root).

Альтернативный более простой подход: если перед Write для того же file_path был Read tool call в той же сессии → `modified`. Это покрывает практически все реальные случаи (Claude читает файл перед перезаписью).

---

## Scope

- Изменить классификацию Write tool calls: проверять наличие предшествующего Read для того же пути
- Опционально: использовать git diff для дополнительной проверки

## Out of scope

- Ретроактивное исправление исторических записей
- Обработка Write на файлы вне git-репозитория

---

## Как протестировать

1. Провести сессию где файл читается (Read) и потом перезаписывается (Write)
2. Запустить `archive-current`
3. Проверить `session_artifacts` — action должен быть `modified`, не `created`
4. Провести сессию где создаётся новый файл (только Write, без предшествующего Read)
5. Проверить — action = `created`

## Критерии приёмки

1. Read → Write на один файл → action = `modified`
2. Write без предшествующего Read на новый файл → action = `created`
3. Git status `M` для файла при Write → action = `modified`
