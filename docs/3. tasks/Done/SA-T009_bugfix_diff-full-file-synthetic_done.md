**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T009 — Исправить diff: весь файл как новый для untracked/large файлов

## Customer-facing инкремент

После исправления diff-блоки в архиве будут показывать реальные изменения сессии (добавленные строки), а не весь файл целиком. Не нужно вручную заменять `@@ -0,0 +1,1658 @@` на минимальный diff после каждой архивации.

---

## Баги

### BUG-DIFF-SCOPE — synthetic diff показывает весь файл как новый

**Симптом:** Diff для изменённого файла выглядит как `@@ -0,0 +1,N @@` (N = число строк файла) — как будто файл создан с нуля. Реальные изменения составляют 20–50 строк в нескольких местах.

**Root cause:** `_synthetic_diff_for_artifact()` использует `git diff HEAD -- <file>` как источник diff. Для untracked файлов (нет git истории, файл не добавлен в git) этот вызов возвращает пустой output. Fallback: показывает весь текущий контент файла как `+`. Результат — `@@ -0,0 +1,N @@`.

**Повторялось:** 13+ раз, каждый раз исправляется вручную.

**Fix:**
```python
def _synthetic_diff_for_artifact(file_path, session_cwd):
    # 1. Попробовать git diff (для tracked файлов)
    result = subprocess.run(['git', 'diff', 'HEAD', '--', file_path], ...)
    if result.stdout.strip():
        return result.stdout, 'git_head'

    # 2. Если файл untracked — проверить размер
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        line_count = _count_lines(file_path)
        if line_count > 300:  # файл слишком большой для full-file diff
            return None, 'manual'  # → запись diff_source='manual', без diff-блока

    # 3. Маленький untracked файл — можно показать как created
    content = open(file_path).read()
    return _format_as_new_file(content), 'synthetic_new'
```

---

### BUG-DIFF-WRONG-HUNK — ошибка чтения файла попадает в diff

**Симптом:** `BUGS.md` diff выглядит как `@@ -1 +1,3438 @@` — строка "before" = текст ошибки `"File content (341.3KB) exceeds maximum allowed size"`. Весь файл показан как новый.

**Root cause:** `_synthetic_diff_for_artifact()` читает файл через Read tool для snapshot "до". Если файл >256KB — Read возвращает error-строку. Эта error-строка становится `before`-контентом → diff показывает весь файл как изменённый от одной error-строки.

**Повторялось:** 6+ раз (каждый раз при архивации сессий с изменением BUGS.md).

**Fix:**
```python
# Перед read-snapshot — проверить размер файла
def _read_file_snapshot(file_path):
    stat = os.stat(file_path)
    if stat.st_size > 200_000:  # >200KB
        return None  # → diff_source='manual'
    return open(file_path, 'r', errors='replace').read()
```

---

## Scope

- В `_synthetic_diff_for_artifact()`: добавить проверку размера файла перед генерацией diff
- Если файл >300 строк и untracked → `diff_source='manual'`, не генерировать full-file diff
- Если file read возвращает error-строку (содержит "exceeds maximum") → `diff_source='manual'`
- Добавить threshold-константу `SYNTHETIC_DIFF_MAX_LINES = 300`

## Out of scope

- Реальный git tracking для untracked файлов (это задача пользователя)
- Diff для бинарных файлов

---

## Как протестировать

1. Провести сессию с изменением `session_archive.py` (untracked, ~1600 строк)
2. Запустить `/archive-session`
3. Проверить diff для `session_archive.py` — должен быть `diff_source='manual'`, не `@@ -0,0 +1,1600 @@`
4. Провести сессию с изменением `BUGS.md` (>256KB)
5. Проверить diff — должен быть `manual`, не `@@ -1 +1,3438 @@`

## Критерии приёмки

1. Файл >300 строк и untracked → diff = отсутствует, `diff_source='manual'`
2. Файл >200KB → diff = отсутствует, `diff_source='manual'`
3. Error-строка Read не попадает в diff-контент
4. Tracked файлы с реальным git diff продолжают работать корректно
