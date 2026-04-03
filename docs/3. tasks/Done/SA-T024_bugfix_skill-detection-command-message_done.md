**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T024 — Исправить детекцию скиллов через command-message механизм

## Customer-facing инкремент

После архивирования сессии skill-теги включают все реально запущенные скиллы — в том числе вызванные через `/skillname` командную строку, не только через Skill tool call.

---

## Баги

### BUG-SKILL-TAGS-SLASH-COMMAND — скиллы через `/skillname` не детектируются

**Симптом:** В сессии `a76647d6` использовались `/intro`, `/accept`, `/archive-session`, `/verify-archive`, но skill tags оказались пустыми. Скиллы детектировались только вручную.

**Root cause:** После SA-T012 детекция скиллов перенесена исключительно на Skill tool calls в JSONL: `{"name": "Skill", "input": {"skill": "..."}}`. Но когда пользователь вводит `/archive-session` в Claude Code, это не создаёт Skill tool call — вместо этого промпт инжектируется напрямую в user-message через `<command-message>archive-session</command-message>` и `<command-name>/archive-session</command-name>`.

**Повторялось:** 2+ раза, каждый раз добавляются вручную.

**Fix:**
```python
def detect_skills(messages):
    skills = set()

    for msg in messages:
        if msg.get('role') != 'user':
            continue

        # 1. Skill tool call (уже реализовано)
        for tc in msg.get('tool_calls', []):
            if tc.get('name') == 'Skill':
                skill_name = tc.get('input', {}).get('skill', '')
                if skill_name:
                    skills.add(skill_name)

        # 2. command-name tag из user message (НОВОЕ)
        # Ищем <command-name>/skillname</command-name> в начале сообщения
        text = msg.get('text', '') or ''
        # Ограничиваем поиск первыми 500 символами, чтобы не захватить контент скилла
        head = text[:500]
        for m in re.finditer(r'<command-name>/?([^<]+)</command-name>', head):
            skill_name = m.group(1).lstrip('/')
            # Только если имя похоже на скилл (не XML-атрибут)
            if re.match(r'^[a-z][a-z0-9-]*$', skill_name) and skill_name not in RESERVED_XML_NAMES:
                skills.add(skill_name)

        # 3. command-message tag (как fallback для старых форматов)
        for m in re.finditer(r'<command-message>([^<]+)</command-message>', head):
            skill_name = m.group(1).strip()
            if re.match(r'^[a-z][a-z0-9-]*$', skill_name) and skill_name not in RESERVED_XML_NAMES:
                skills.add(skill_name)

    return list(skills)

# RESERVED_XML_NAMES — XML-теги Claude CLI, не скиллы:
RESERVED_XML_NAMES = {
    'command-args', 'command-message', 'command-name', 'ide', 'output-file',
    'private', 'status', 'subagents', 'summary', 'task-id', 'task-notification',
    'tool-use-id', 'ide_opened_file', 'user-prompt-submit-hook'
}
```

---

### BUG-TAGS-SKILL-MISSING — `bugs-to-task` и похожие скиллы не детектируются

**Симптом:** В сессии `3ec9d7e1` (`/bugs-to-task` явно использовался) skill tag `bugs-to-task` отсутствовал. `detect_skills()` не нашёл ни Skill tool call, ни `/skillname` строку — только инжектированный промпт.

**Root cause:** То же что BUG-SKILL-TAGS-SLASH-COMMAND. Дополнительно: скилл может быть записан в JSONL как `<command-message>bugs-to-task</command-message>` без `/` префикса.

**Повторялось:** 1+ раз.

**Fix:** Покрывается тем же исправлением в `detect_skills()` выше (пункт 3 — command-message fallback).

---

## Scope

- В `detect_skills()` добавить парсинг `<command-name>` и `<command-message>` тегов из user-сообщений
- Ограничить поиск первыми 500 символами (до начала инжектированного контента скилла)
- Фильтровать по списку `RESERVED_XML_NAMES` (исключить XML-атрибуты Claude CLI)
- Добавить regex-валидацию: только `^[a-z][a-z0-9-]*$` считается именем скилла

## Out of scope

- Детекция скиллов из prose (уже исключено в SA-T012)
- Изменение формата JSONL

---

## Как протестировать

1. Запустить `/archive-session` в тестовой сессии
2. Проверить что session_tags содержит `skill:archive-session`
3. Проверить что `skill:command-name` и `skill:command-message` НЕ появляются

## Критерии приёмки

1. `/archive-session` через command-message → `skill:archive-session` в tags
2. `/bugs-to-task` через command-message → `skill:bugs-to-task` в tags
3. XML-атрибуты (`command-name`, `command-message`, `ide`) НЕ попадают в skill tags
