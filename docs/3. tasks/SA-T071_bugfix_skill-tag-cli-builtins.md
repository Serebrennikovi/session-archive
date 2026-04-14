**Дата:** 2026-04-09
**Статус:** open
**Severity:** LOW

# SA-T071 — CLI builtin команды (/model, /help, /clear) попадают в skill tags

## Проблема

`/model opus`, `/help`, `/clear`, `/compact` — встроенные CLI-команды Claude Code, не пользовательские скиллы. Они записываются в JSONL как `<command-name>/model</command-name>` + `<command-message>model</command-message>`, и `detect_skills()` из SA-T024 считает их скиллами, потому что `model` проходит regex-валидацию (`^[a-z][a-z0-9-]*$`) и не входит в `RESERVED_XML_NAMES`.

## Воспроизведение — session fb6419f7 (sproektirui, 2026-04-09)

1. Пользователь ввёл `/model opus` в середине сессии
2. В JSONL записано: `<command-name>/model</command-name>` + `<command-args>opus</command-args>`
3. Парсер извлёк `skill: model` в session_tags
4. Тег ложный — `/model` не скилл, а встроенная команда CLI

## Root cause

SA-T024 добавил `RESERVED_XML_NAMES` для исключения XML-тегов (`command-name`, `ide`, etc.), но не добавил список CLI builtin команд. Команды вида `/model`, `/help`, `/clear`, `/compact`, `/cost`, `/login`, `/logout`, `/status`, `/config`, `/fast` проходят regex-валидацию как скиллы.

## Рекомендация по фиксу

Добавить `CLI_BUILTIN_COMMANDS` set в `detect_skills()`:

```python
CLI_BUILTIN_COMMANDS = {
    'model', 'help', 'clear', 'compact', 'cost', 'login', 'logout',
    'status', 'config', 'fast', 'doctor', 'init', 'mcp', 'permissions',
    'review', 'terminal-setup', 'memory', 'bug',
}
```

Фильтр: `if skill_name not in RESERVED_XML_NAMES and skill_name not in CLI_BUILTIN_COMMANDS`.

## Прецедент #2 — session d3dae777 (sproektirui, 2026-04-09)

Пользователь ввёл `/model opus`. Парсер записал `skill: model`. Исправлено вручную при verify-archive.

## Связанные баги

- SA-T024 (done) — детекция скиллов через command-message/command-name (исходный фикс)
- SA-T020 (done) — phantom skill tags (предшественник)
