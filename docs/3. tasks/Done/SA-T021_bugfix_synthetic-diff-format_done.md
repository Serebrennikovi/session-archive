**Дата:** 2026-04-03
**Статус:** done 2026-04-03
**Спецификация:** —

# SA-T021 — Исправить synthetic diff: пустые строки и ложный full-file add

## Customer-facing инкремент

После архивирования сессии `## Diffs` для untracked и modified файлов будет показывать реальный session-local patch без пустых строк между строками кода. Modified файлы не будут отображаться как `@@ -0,0 +1,N @@` (создание с нуля).

---

## Баги

### BUG-40 — Synthetic diff даёт пустые строки и ложный full-file add

**Симптом:** Для локальных doc/task файлов (untracked или dirty-worktree) `## Diffs` некорректен сразу по двум осям:
1. Пустая строка между каждой строкой кода: `+line1\n\n+line2\n\n+line3`
2. Весь файл показывается как новый: `@@ -0,0 +1,N @@`, хотя в сессии только дописывали review-блок в конец существующего файла

**Root cause:** Архиватор не удерживает надёжный session-local baseline для файлов вне git. Synthetic fallback:
- ломает переносы строк при рендере diff-блока (лишний `\n` после каждой строки)
- считает modified file "новым" когда git history отсутствует (`@@ -0,0`)

**Повторялось:** 11+ раз, каждый раз исправляется вручную Python-скриптом.

**Fix:**
```python
# При генерации synthetic diff:
# 1. Убрать двойные newlines
diff_lines = [line.rstrip('\n') for line in diff_content.split('\n')]
diff_output = '\n'.join(diff_lines)  # не '\n\n'.join

# 2. Если файл читался ранее в сессии — использовать earliest read как baseline
def get_baseline(file_path, session_messages):
    for msg in session_messages:
        for tool_result in msg.get('tool_results', []):
            if tool_result.get('file_path') == file_path:
                return tool_result.get('content', '')
    return None  # новый файл

baseline = get_baseline(file_path, session_messages)
if baseline is not None:
    # строим реальный unified diff от baseline
    diff = unified_diff(baseline.splitlines(), after.splitlines(), ...)
else:
    # помечаем как "new file in session", не @@ -0,0 fallback
    diff = format_new_file_diff(after)
```

---

### BUG-DIFF-FMT — пустые строки в synthetic diff (все 5 подтверждений)

**Симптом:** Только synthetic diff (новые/untracked файлы) имеет паттерн `+line\n\n+line`. git_head дифы (изменения в отслеживаемых файлах) корректны. Баг только в synthetic fallback пути.

**Root cause:** В `diff_source=edit_snippet` построчная генерация добавляет `\n` после каждой строки; при объединении в блок получается двойной `\n\n`. Git-based diff не проходит через этот код path.

**Повторялось:** 5+ раз подряд (каждая сессия с untracked файлами).

**Fix:**
- В synthetic diff builder: `line.rstrip('\n')` перед добавлением в буфер
- Тест: `assert '\n\n+' not in synthetic_diff_output`

---

### BUG-12 — Modified untracked файлы архивируются как full-file add from empty

**Симптом:** Для файлов типа `ADV-T012...md` и `ADV-T013...md` (существующие untracked task docs): diff показывает `@@ -0,0 +1,N @@` — как будто файл создан с нуля. В реальности файл существовал, в сессии его читали (Read tool output), затем изменяли (apply_patch / Edit).

**Root cause:** Для untracked файлов архиватор пытается строить diff от git-baseline (которого нет) и не использует session-start snapshot / earliest Read output как левую сторону diff.

**Повторялось:** 5+ раз, каждый раз исправляется вручную.

**Fix:**
- Если файл untracked, но ранее в этой же сессии уже читался (есть Read tool call с этим путём) → строить diff от содержимого самого раннего Read как `before_text`
- Если baseline из Read недоступен и файл физически существует на диске → читать текущий контент как `after_text`, искать before в session history
- Если baseline совсем нет → помечать `(new file in session)`, не ложный `@@ -0,0`

```python
def build_diff_for_untracked(file_path, after_text, session_messages):
    # Ищем earliest Read tool call на этот файл
    before_text = find_earliest_read(file_path, session_messages)
    if before_text is not None:
        return unified_diff(before_text.splitlines(), after_text.splitlines(),
                           fromfile=f'a/{file_path}', tofile=f'b/{file_path}')
    else:
        # Явно новый файл — правильный hunk, не @@ -0,0 с пустыми строками
        return format_new_file_diff(file_path, after_text)
```

---

## Scope

- Исправить synthetic diff builder: убрать двойные `\n` между строками
- Добавить session-local baseline lookup из earliest Read tool call
- Корректно различать "новый файл" vs "modified untracked" в diff output

## Out of scope

- Изменение git-based diff (только synthetic fallback)
- Изменение логики для tracked файлов (они работают корректно)

---

## Как протестировать

1. Запустить `archive-current` на сессии где редактировался untracked task doc
2. Проверить `## Diffs` — нет паттерна `+line\n\n+line` (двойных newlines между строками)
3. Проверить что untracked modified файл не показывает `@@ -0,0 +1,N @@` если он читался ранее в сессии
4. Новый файл (не читался до создания) показывает корректный `@@ -0,0 +1,N @@` без пустых строк

## Критерии приёмки

1. `'\n\n+' not in diff_output` для всех synthetic diff блоков
2. Untracked modified файл (Read + Edit в сессии) даёт unified diff с реальными hunks, не full-file add
3. Реально новый файл (без Read до создания) корректно помечен как новый файл
