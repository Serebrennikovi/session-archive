**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T025 — Исправить PROJECT_SLUG: underscore → dash

## Customer-facing инкремент

После исправления `archive-current` автоматически находит JSONL-файлы для проектов, в пути которых есть подчёркивание (например `12_SessionArchive`), без ручного указания пути.

---

## Баги

### BUG-SLUG-UNDERSCORE-TO-DASH — `_` в PROJECT_SLUG не заменяется на `-`

**Симптом:** В сессии `d9b0110c` (проект `12_SessionArchive`): `PROJECT_SLUG` вычислялся по `sed 's|/|-|g'` и давал `12_SessionArchive`, тогда как реальная директория Claude называется `12-SessionArchive` (Claude Code заменяет и `/`, и `_` на `-`). Скрипт не находил JSONL → поиск шёл в неверной директории.

SA-T005 исправил leading dash (`-Users-is-...`), но не underscore.

**Root cause:** Claude Code при создании директорий проектов в `~/.claude/projects/` заменяет все `/` и `_` на `-`. Скрипт в `archive-session` skill использует только `sed 's|/|-|g'`, пропуская `_` → `-` замену.

**Повторялось:** 1+ раз.

**Fix:**
В `archive-session.md` skill (и в любом месте где вычисляется PROJECT_SLUG):

```bash
# Старый код:
PROJECT_SLUG=$(echo "$PWD" | sed 's|^/|-|; s|/|-|g')

# Новый код — дополнительно заменяем _ на -:
PROJECT_SLUG=$(echo "$PWD" | sed 's|^/|-|; s|/|-|g; s|_|-|g')

# Альтернатива через Python (более надёжно):
PROJECT_SLUG=$(python3 -c "
import sys
path = sys.argv[1]
slug = path.replace('/', '-').replace('_', '-')
if not slug.startswith('-'):
    slug = '-' + slug
print(slug)
" "$PWD")
```

Дополнительно — добавить fuzzy-поиск директории как fallback:

```bash
# Если точный путь не найден, поискать по basename проекта
JSONL_DIR="$HOME/.claude/projects/${PROJECT_SLUG}"
if [ ! -d "$JSONL_DIR" ]; then
    # Fuzzy fallback: grep по последнему компоненту пути
    PROJECT_NAME=$(basename "$PWD" | tr '_' '-')
    JSONL_DIR=$(ls -d "$HOME/.claude/projects/"*"${PROJECT_NAME}" 2>/dev/null | head -1)
fi
```

---

## Scope

- Обновить формулу `PROJECT_SLUG` в `archive-session.md` skill: добавить `s|_|-|g`
- Добавить fuzzy-fallback поиск директории по `basename` если точный slug не найден
- Проверить наличие аналогичного кода в `session_archive.py` и обновить там же

## Out of scope

- Изменение способа именования директорий Claude Code
- Переименование существующих JSONL-директорий

---

## Как протестировать

1. В проекте с `_` в пути (например `/Users/is/personal/Projects/12_SessionArchive`)
2. Запустить `archive-current` → убедиться что находит JSONL без ручного указания пути
3. Проверить что `PROJECT_SLUG` = `-Users-is-personal-Projects-12-SessionArchive`

## Критерии приёмки

1. `PROJECT_SLUG` для пути `12_SessionArchive` = `-Users-is-...-12-SessionArchive` (с `-` вместо `_`)
2. JSONL находится автоматически для проектов с `_` в пути
