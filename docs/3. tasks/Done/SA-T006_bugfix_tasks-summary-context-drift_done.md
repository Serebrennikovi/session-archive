**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T006 — Исправить Tasks и Summary: дрейф из контекста

## Customer-facing инкремент

После исправления `session_tasks` и `sessions.summary` будут отражать только реально выполненные задачи сессии — без задач из HANDOFF-таблиц, skill-примеров и упомянутого контекста.

---

## Баги

### BUG-27 / BUG-39 / BUG-17 — Summary и Tasks дрейфуют к skill/context-тексту

**Симптом:** `Summary` ссылается на задачи из примеров скиллов (`T097`, `T123`) или промежуточного commentary. `session_tasks` содержит `T097`, `T123`, `T139`, `T140`, `T141` вместо единственной реально ревьюируемой задачи. Повторяется во всех Codex и Claude сессиях sproektirui и других проектов.

**Root cause:** Парсер задач (`extract_tasks()` или аналог) ищет паттерны `T\d+` по всему тексту JSONL, включая:
- тела system-промптов скиллов (где `T097`, `T123` — примеры)
- сообщения-результаты Read-тула (прочитанный HANDOFF.md содержит всю таблицу задач)
- prose-комментарии ассистента (`"как и в T013..."`)

Задача попадает в список если упомянута, а не если реально обрабатывалась.

**Повторялось:** 22+ раз (BUG-27 — 22 сессии, BUG-39 — 8, BUG-17 — 5).

**Fix:**
Ограничить источники для task-detection только инструментальными действиями:
1. Write/Edit на файл `docs/3. tasks/SA-TXXX_*.md` → задача `edited`
2. Bash-команда `mv ... Done/` → задача `completed`
3. Явные слова `T\d+` в user-сообщениях (не в tool_result)

Исключить из парсинга:
- `tool_result` блоки (результаты Read, Bash)
- `content` блоки с `type=text` внутри system-промптов
- Assistant-prose без инструментального действия на файл задачи

```python
# Псевдокод фикса в extract_tasks():
TASK_SOURCES = ['user_message', 'tool_use']  # только эти
# Не 'tool_result', не 'system'

for msg in messages:
    if msg['role'] not in TASK_SOURCES:
        continue
    # Для tool_use — только если input.file_path содержит 'tasks/'
    if msg['type'] == 'tool_use':
        if 'tasks/' not in msg.get('input', {}).get('file_path', ''):
            continue
    tasks.update(re.findall(r'T\d+', msg['content']))
```

---

### BUG-TASKS / BUG-TASKS-FROM-CONTEXT — Tasks из HANDOFF-контекста

**Симптом:** `session_tasks` содержит `T143`, `T001`, `T002` и другие задачи из прочитанного HANDOFF.md, хотя реально работали только с одной задачей. Повторяется каждый раз, когда сессия начинается с `/intro` (читает HANDOFF).

**Root cause:** Тот же что у BUG-27 — `tool_result` от Read-вызова на HANDOFF.md содержит всю таблицу задач с номерами `T\d+`. Парсер захватывает их все.

**Повторялось:** 8 (BUG-TASKS) + 6 (BUG-TASKS-FROM-CONTEXT) = 14 раз.

**Fix:** Тот же что выше — исключить `tool_result` из task-detection.

---

## Scope

- Изменить `extract_tasks()` (или аналогичную функцию) в `session_archive.py`
- Исключить `tool_result` и system-блоки из sources для T\d+ паттернов
- Добавить эвристику: задача считается реальной если был Write/Edit на файл задачи ИЛИ задача явно упомянута в user-сообщении

## Out of scope

- Summary-генерация (отдельный баг BUG-SUMMARY-MISMATCH)
- Изменение структуры БД

---

## Как протестировать

1. Запустить `/archive-session` на сессии где читался HANDOFF.md (через `/intro`)
2. Проверить `session_tasks` — должны быть только задачи из реальных Write/Edit вызовов на файлы tasks/
3. Проверить что T-номера из текста HANDOFF.md не попали в список

## Критерии приёмки

1. `session_tasks` содержит только задачи, файлы которых реально менялись в сессии (или явно упомянуты в user-сообщениях)
2. После `/intro` (Read на HANDOFF) задачи из HANDOFF-таблицы не появляются автоматически
3. Баг BUG-27 не воспроизводится в тестовой сессии с codereview одной задачи
