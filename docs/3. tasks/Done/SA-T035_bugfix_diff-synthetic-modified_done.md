**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T035 — Исправить Diff: whole-file synthetic для modified untracked + wrong-file из worktree

## Customer-facing инкремент

После архивирования сессии `## Diffs` покажут реальные изменения текущей сессии — конкретные hunks с добавленными/удалёнными строками — а не весь файл как новый или diff чужих uncommitted изменений.

---

## Баги

### BUG-DIFF-SYNTHETIC — modified файл без base_commit → diff `@@ -0,0 +1,N @@`

**Симптом:** Когда файл существовал до сессии (modified, не created) но не отслеживается git или не имеет `base_commit`, diff builder генерирует `@@ -0,0 +1,N @@` — весь текущий файл как "новый":

```diff
--- /dev/null
+++ b/docs/3. tasks/T144_cache-invalidation.md
@@ -0,0 +1,83 @@
+# T144 — Cache invalidation
+...
+(83 строки целиком)
```

Хотя в реальности в сессии были изменены только 2 фрагмента файла.

Примеры:
- `e67a5b19` (sproektirui): `T144_*.md` — существовал до сессии, показан как новый (83 строки)
- `88a8e972` (autodev-v2): `pre_analysis_T141.md` — существовал, мы правили 2 места (добавили INVARIANT, исправили шаг 4), показан как `@@ -0,0 +1,58 @@`

**Root cause:** Когда `base_commit` не определён (`-`) и файл не в git (untracked `??`) или git не может найти его в HEAD, diff builder падает в fallback `synthetic` — берёт текущее содержимое файла и показывает как добавление от пустоты. Логика: "нет предыдущей версии → всё новое".

**Повторялось:** 2+ раза, плюс BUG-DIFF-SETTINGS-SYNTHETIC в отдельной сессии.

**Fix:**

Приоритетный источник "before" для diff:

1. **Before-snapshot из Read tool** — если тот же файл был прочитан через Read tool в текущей сессии до его изменения, взять вывод Read как `before`. Построить diff через `difflib.unified_diff(before_lines, after_lines)`.

2. **Before-snapshot из cat/sed** — аналогично для Bash tool reads.

3. **Edit/apply_patch content** — если было `str_replace_editor` с `old_string`/`new_string`, построить patch из этих данных напрямую, не из файловой системы.

4. **`git show HEAD:file`** — если файл tracked в git, взять последний коммит.

5. **`git diff HEAD~1 -- file`** — если файл в git и был недавно закоммичен.

6. **Fallback**: synthetic с явной пометкой `diff_source=synthetic_no_base` в БД (не `@@ -0,0 +1,N @@` как "новый", а хотя бы honest label).

---

### BUG-DIFF-WRONG-FILE — `git diff HEAD` захватывает файлы из предыдущих uncommitted sessions

**Симптом:** Diff builder использует `git diff HEAD` (или `git diff HEAD -- .`) без scope-ограничения. Результат: diff показывает ВСЕ uncommitted изменения в worktree, включая файлы из предыдущих сессий которые не были закоммичены.

Пример из `eba39d60`:
- Текущая сессия: изменён только `T146_*.md` (untracked `??`)
- В worktree pre-existing uncommitted: `T145_*.md` (тоже `??` из предыдущей сессии)
- Результат diff: показан `T145` (pre-existing), `T146` (реальный) — отсутствует вовсе

**Root cause:** Diff builder строит diff от `base_commit` до HEAD или от HEAD до worktree без фильтрации по списку артефактов текущей сессии. Любые "грязные" файлы в worktree попадают в результат.

**Повторялось:** 1+ раз явно, вероятно присутствует в других сессиях незамеченным.

**Fix:**

Строить diff только для файлов, которые есть в `session_artifacts` текущей сессии (artifact_path list). Никогда не использовать `git diff HEAD -- .` (весь worktree). Всегда указывать конкретный путь:

```python
for artifact in session_artifacts:
    if artifact.action in ('created', 'modified'):
        diff = build_diff_for_file(artifact.path, before_snapshot, after_snapshot)
```

---

## Scope

- Добавить before-snapshot extractor: ищет Read tool output для пути файла до его изменения
- Использовать `difflib.unified_diff` для построения реального diff при наличии before-snapshot
- Ограничить `git diff` только файлами из `session_artifacts` (не `git diff HEAD -- .`)
- Добавить `diff_source` поле в БД если его нет: `git_head`, `read_snapshot`, `edit_snippet`, `synthetic_no_base`

## Out of scope

- Исправление уже записанных diff-блоков в БД
- Поддержка binary файлов

---

## Как протестировать

1. Сессия где читается и изменяется untracked файл → diff должен показать только изменённые строки, не весь файл
2. Сессия с pre-existing uncommitted файлами в worktree + изменение другого файла → diff должен показать только файл из текущей сессии
3. Сессия с `str_replace_editor` (old_string/new_string) → diff должен соответствовать exactly этому edit

## Критерии приёмки

1. Diff для modified (не created) файла никогда не содержит `@@ -0,0 +1,N @@` если файл существовал до сессии и был прочитан
2. Diff строится только для файлов из `session_artifacts` текущей сессии
3. `diff_source` в БД: `read_snapshot` если before взят из Read output, `git_commit` если из git
