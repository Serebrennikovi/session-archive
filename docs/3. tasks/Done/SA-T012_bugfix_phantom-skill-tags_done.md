**Дата:** 2026-04-03
**Статус:** done
**Выполнено:** 2026-04-03
**Спецификация:** —

# SA-T012 — Исправить фантомные skill-теги (XML-маркеры + phantom skills)

## Customer-facing инкремент

После архивирования сессии теги `skill:` содержат только реально использованные навыки. Не нужно вручную удалять `command-message`, `command-name`, `dev`, `ide`, `subagents` из каждого архива.

---

## Баги

### BUG-SKILL-XML — XML-маркеры `<command-message>/<command-name>` попадают в skill-теги

**Симптом:** `session_tags` содержит `skill: command-message`, `skill: command-name` — эти значения берутся из XML-маркеров `<command-message>/<command-name>` в system-reminder или теле диалога. Реальными скиллами они никогда не являются.

**Root cause:** Теггер ищет skill-имена регексом по всему тексту сообщений (включая `<command-message>` теги из system-reminder). Нет фильтрации по источнику.

**Повторялось:** 8+ раз, каждый раз удаляется вручную.

**Fix:**
```python
# Blacklist XML-маркеров которые никогда не являются skill-именами
SKILL_TAG_BLACKLIST = {
    'command-message', 'command-name', 'system-reminder',
    'ide_selection', 'ide_opened_file', 'user-prompt-submit-hook',
}

def extract_skill_tags(messages):
    skills = set()
    for msg in messages:
        if msg['role'] != 'assistant':
            continue
        # Только из реальных Skill tool calls, не из текста
        for tool_call in msg.get('tool_calls', []):
            if tool_call['name'] == 'Skill':
                skill_name = tool_call['input'].get('skill', '')
                if skill_name and skill_name not in SKILL_TAG_BLACKLIST:
                    skills.add(skill_name)
    return skills
```

---

### BUG-SKILL-PHANTOM — `dev`, `ide`, `subagents`, `visualcheck` без реальных вызовов

**Симптом:** `session_tags` содержит `skill: dev`, `skill: ide`, `skill: subagents`, `skill: visualcheck` — хотя соответствующих Skill tool calls в сессии не было. Теги добавляются из упоминаний в тексте (/dev запущен, использован ide и т.д.).

**Root cause:** Теггер матчит skill-имена из prose-текста ассистента и пользователя, не только из фактических `Skill` tool calls.

**Повторялось:** 8+ раз.

**Fix:**
- Skill-теги должны добавляться ИСКЛЮЧИТЕЛЬНО из Skill tool calls (см. fix BUG-SKILL-XML выше).
- Дополнительный whitelist известных скиллов для валидации:

```python
KNOWN_SKILLS = {
    'archive-session', 'verify-archive', 'intro', 'codereview',
    'fix', 'accept', 'dev', 'qa', 'pm', 'ux', 'team', 'autodev',
    'autoresearch', 'next', 'bugs-to-task', 'shotgun', 'loop',
    # etc — загружать из ~/.claude/commands/ динамически
}

# Если skill не в whitelist — логировать предупреждение, не добавлять тег
if skill_name not in KNOWN_SKILLS:
    logger.warning(f"Unknown skill in tool call: {skill_name!r}")
```

---

## Scope

- Переписать `extract_skill_tags()`: только Skill tool calls, не prose
- Добавить `SKILL_TAG_BLACKLIST` с XML-маркерами
- Опционально: загружать список известных скиллов из `~/.claude/commands/`

## Out of scope

- Детекция навыков по косвенным признакам (если Skill tool недоступен)
- Изменение логики domain-тегов (это SA-T008)

---

## Как протестировать

1. Взять сессию с `<command-message>bugs-to-task</command-message>` в system-reminder
2. Запустить `/archive-session`
3. Проверить: `command-message` и `command-name` отсутствуют в `session_tags`
4. Проверить: `bugs-to-task` присутствует в `session_tags` (если Skill tool был вызван)
5. Взять сессию где `/dev` упоминается в тексте но Skill не вызывался
6. Проверить: `dev` отсутствует в `session_tags`

## Критерии приёмки

1. `command-message`, `command-name` никогда не появляются в `session_tags`
2. `dev`, `ide`, `subagents` добавляются только при наличии Skill tool call с этим именем
3. Skill-теги совпадают с реально вызванными навыками из JSONL
