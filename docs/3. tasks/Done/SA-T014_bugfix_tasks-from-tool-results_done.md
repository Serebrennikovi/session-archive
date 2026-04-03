**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T014 — Исправить task IDs из content tool-результатов

## Customer-facing инкремент

После архивирования `session_tasks` содержит только реально обрабатываемые задачи. Задачи из содержимого прочитанных файлов (Read/Grep/Bash tool results) не попадают в список.

---

## Баги

### BUG-TASKS-FROM-TOOL-RESULTS — task IDs из содержимого прочитанных файлов

**Симптом:** `session_tasks` содержит фантомные task IDs — например `T042` — которые никогда не были задачами текущей сессии. Они появляются из содержимого файлов, прочитанных инструментом Read/Grep/Bash. В JSONL эти данные попадают в поле `tool_result`.

**Пример из сессии 54332c00 (2026-04-03):** в `session_tasks` появился `T042`, хотя в сессии работали только с T017. T042 попал из содержимого одного из прочитанных файлов (предположительно из сессионного экспорта открытого в IDE или из Bash-вывода).

**Root cause:** SA-T006 исправил дрейф задач из текста `assistant` и `user` сообщений, но `detect_tasks()` до сих пор сканирует `tool_result` контент (ответы Read/Grep/Bash). Паттерн `T\d+` находит ID в любом тексте:
- содержимое прочитанных HANDOFF и спецификаций (например, "T042" упомянут в задаче, которую мы не брали)
- вывод Grep/Bash команд
- содержимое открытых в IDE файлов (ide_opened_file events)

**Повторялось:** 1+ раз (обнаружен 2026-04-03 при verify-archive сессии 54332c00).

**Fix:**

Ограничить источник task_id — только сообщения ассистента (не tool_result):

```python
def detect_tasks(messages: list[dict]) -> list[str]:
    """Detect task IDs from assistant messages only, not from tool results."""
    task_ids = set()
    TASK_PATTERN = re.compile(r'\bT(\d{3,})\b')  # T017, T042, etc.

    for msg in messages:
        # Only assistant messages, NOT tool_result content
        if msg.get('role') != 'assistant':
            continue
        text = msg.get('text', '') or ''
        for match in TASK_PATTERN.finditer(text):
            task_ids.add(f"T{match.group(1)}")

    return sorted(task_ids)
```

Дополнительно: проверять что найденный task ID фигурирует в действии (создание файла задачи, чтение файла задачи с action=modified), а не просто упоминается.

---

## Scope

- Изменить `detect_tasks()` в `session_archive.py`: сканировать только `role=assistant` сообщения, не `tool_result`
- Не менять логику обнаружения через artifact file_path (задачи из реально прочитанных/изменённых файлов задач — валидный источник)

## Out of scope

- Проверка что task_id существует в HANDOFF (слишком сложно, требует доступа к проекту)
- Ретроактивное исправление исторических записей

---

## Как протестировать

1. Запустить сессию где HANDOFF содержит 10+ task IDs, но работаем только с одним
2. Запустить `archive-current`
3. Проверить `session_tasks` — должен быть только реально обрабатываемый task

## Критерии приёмки

1. `session_tasks` не содержит task IDs из содержимого Read/Grep tool results
2. Task ID из названия файла, реально изменённого в сессии (например `ADV-T017_...md`), присутствует
3. Task IDs из HANDOFF (не изменявшегося в сессии) не попадают в список
