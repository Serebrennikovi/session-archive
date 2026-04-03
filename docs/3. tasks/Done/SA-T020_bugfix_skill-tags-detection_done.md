**Дата:** 2026-04-03
**Статус:** done
**Завершено:** 2026-04-03
**Спецификация:** —

# SA-T020 — Исправить детекцию skill-тегов: missing и timing

## Customer-facing инкремент

После архивирования сессии skill-теги (`intro`, `archive-session`, `verify-archive`) будут соответствовать реально выполненным навыкам. Навыки, запрошенные после archive boundary, не попадут в запись текущей сессии.

---

## Баги

### BUG-SKILL-MISSING — реально вызванные скиллы не появляются в тегах

**Симптом:** `intro`, `archive-session`, `verify-archive` — все три запускались явно через Skill tool, но в `session_tags` (category=skill) отсутствуют. Вместо них появляются фантомные теги (`command-message`, `command-name`, `dev`, `ide`, `subagents`) из XML-маркеров и prose в диалоге.

**Root cause:** Skill detection не парсит фактические вызовы Skill tool в JSONL. Вместо этого он сканирует текст сообщений на упоминания skill-имён, что даёт и ложные positive (из XML-тегов, контекста), и ложные negative (реальные Skill tool calls игнорируются).

**Повторялось:** 10+ раз подряд, каждый раз исправляется вручную.

**Fix:**
```python
# Извлекать skill-теги ТОЛЬКО из tool calls типа Skill
for message in jsonl_messages:
    for tool_call in message.get('tool_calls', []):
        if tool_call.get('name') == 'Skill':
            skill_name = tool_call.get('input', {}).get('skill', '')
            if skill_name:
                add_tag(session_id, 'skill', skill_name)
```
- Не сканировать user/assistant text на skill-имена для построения skill-тегов
- `<command-message>`, `<command-name>` XML-теги в user message → игнорировать (уже частично покрыто SA-T012, но skill-missing остаётся)

---

### BUG-SKILL-TIMING — verify-archive попадает в теги до выполнения

**Симптом:** Тег `skill: verify-archive` проставляется в архивной записи, хотя на момент `archive-current` сам verify ещё не выполнялся. Одновременно отсутствует `skill: session-archive`, который реально был выполнен до archive boundary.

**Root cause:** Skill extraction не учитывает archive boundary — момент вызова `archive-current`. Навыки, упомянутые в плане или запрошенные после archive call, засчитываются наравне с уже выполненными.

**Повторялось:** 5+ раз, каждый раз исправляется вручную.

**Fix:**
- Определить archive boundary: индекс tool call `archive-current` (или `Bash` с аргументом `archive-current`) в JSONL
- Включать в skill-теги только Skill tool calls с индексом < archive boundary
- Skill calls после archive boundary → игнорировать для текущей записи

```python
archive_boundary_idx = find_archive_call_index(jsonl_messages)
for idx, message in enumerate(jsonl_messages):
    if idx >= archive_boundary_idx:
        continue  # после archive — не засчитываем
    for tool_call in message.get('tool_calls', []):
        if tool_call.get('name') == 'Skill':
            ...
```

---

## Scope

- Переписать skill tag extraction: только из Skill tool calls, не из text scanning
- Добавить archive boundary filter для skill tags
- Убрать text-based skill detection как основной метод

## Out of scope

- Изменение других категорий тегов (domain, model, assistant)
- Изменение структуры `session_tags` таблицы

---

## Как протестировать

1. Запустить `archive-current` на сессии где были реальные `/intro` + `/archive-session` Skill calls
2. Проверить `session_tags` — присутствуют `skill: intro`, `skill: archive-session`
3. Проверить что `skill: verify-archive` отсутствует если verify не выполнялся до archive boundary
4. Проверить что `skill: command-message`, `skill: command-name` отсутствуют

## Критерии приёмки

1. Реально вызванные Skill tool calls отражены в `session_tags.category='skill'`
2. Skill calls после archive boundary не попадают в текущую запись
3. `skill: command-message` и `skill: command-name` не генерируются из XML-маркеров
