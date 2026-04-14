---
description: "Сохранить текущую сессию в Session Archive (shared code path)"
---

## AutoResearch Checklist

1. Архивируется ли всегда главный JSONL, а не субагент или случайный файл?
2. Определяется ли session_id корректно (соответствует текущей беседе)?
3. Отражает ли summary реальную работу сессии (не артефакт из чужого контекста)?
4. Работает ли команда без ручного вмешательства — автодетект надёжен в типичных случаях?
5. Обнаруживается ли ошибочный захват автоматически (без необходимости читать вывод и догадываться)?

---

# Archive Session

Логика архивации живёт в `session_archive.py` (в корне репозитория Session Archive), а не в этой команде.
Не воспроизводи вручную шаги поиска JSONL, сборки metadata и записи в SQLite, если это уже умеет shared script.

**Шаг 1 — сформулируй summary сам** по контексту текущего разговора (1-3 предложения: что делали, что нашли, что изменили). Не жди пока скрипт сгенерирует — он не умеет.

**Шаг 2 — собери tool_call_ids из текущей сессии:**

Перечисли все tool_call_ids которые ты использовал в этой сессии (каждый tool_use вызов имеет уникальный id вида `toolu_01...`). Сформируй JSON-массив строк — он будет передан как `--tool-ids` и позволит скрипту точно определить границу сессии в JSONL без cross-session загрязнения.

Пример результата: `TOOL_IDS='["toolu_01abc123", "toolu_02def456"]'`

Если IDs недоступны или сессия очень длинная — оставь `TOOL_IDS=''` (скрипт использует fallback sessionId-фильтр).

**Шаг 3 — найди главный JSONL и запускай с явным путём:**

```bash
# Найти главный JSONL текущей сессии.
# Ищем ТОЛЬКО в директории текущего проекта (по $PWD), сортируем по mtime (новейший первый).
# Claude Code заменяет все / и _ на - при создании директорий проектов.
PROJECT_SLUG=$(echo "$PWD" | sed 's|/|-|g; s|_|-|g')
JSONL_DIR="$HOME/.claude/projects/$PROJECT_SLUG"
MAIN_JSONL=$(ls -t "$JSONL_DIR"/*.jsonl 2>/dev/null | head -1)
echo "JSONL: $MAIN_JSONL"

# Fuzzy fallback: если точный slug не найден — ищем по basename проекта
if [ -z "$MAIN_JSONL" ]; then
  PROJECT_NAME=$(basename "$PWD" | tr '_' '-')
  JSONL_DIR=$(ls -d "$HOME/.claude/projects/"*"${PROJECT_NAME}" 2>/dev/null | head -1)
  if [ -n "$JSONL_DIR" ]; then
    echo "INFO: exact slug '$PROJECT_SLUG' not found, using fuzzy match: $JSONL_DIR"
    MAIN_JSONL=$(ls -t "$JSONL_DIR"/*.jsonl 2>/dev/null | head -1)
  fi
fi

# Если совсем ничего нет — fallback на глобальный поиск:
if [ -z "$MAIN_JSONL" ]; then
  echo "WARNING: нет JSONL в project-dir, fallback на глобальный поиск"
  MAIN_JSONL=$(find ~/.claude/projects/ -name "*.jsonl" -not -path "*/subagents/*" 2>/dev/null | xargs ls -t 2>/dev/null | head -1)
  echo "Fallback JSONL: $MAIN_JSONL"
fi

# Запустить с явным --jsonl (обход бага find_current_jsonl).
# $TOOL_IDS — JSON-массив из шага 2; если пустой — аргумент не передаётся.
TOOL_IDS_ARG=""
[ -n "$TOOL_IDS" ] && TOOL_IDS_ARG="--tool-ids '$TOOL_IDS'"

python3 "$SESSION_ARCHIVE_DIR/session_archive.py" archive-current \
  --agent claude --cwd "$PWD" --jsonl "$MAIN_JSONL" --summary "..." $TOOL_IDS_ARG
```

Не передавай `--jsonl` вручную наугад — только результат команды выше.

Если в `$ARGUMENTS` переданы override-ы:

- `summary=...` → используй как `--summary "..."` вместо своего
- `model=...` → добавь `--model "..."`

После успешного запуска выведи:

- `session_id`
- `agent_family`
- `export_path`
- Количество сообщений — прочитай из export_path строку `| Messages |` и выведи значение
- Есть ли в export секция `## Diffs`
- Если `## Diffs` есть — перечисли пути файлов из этой секции

**Проверка корректности захвата (обязательно):** выполни все три проверки автоматически, без ожидания пользователя:

1. **Проверка проекта:** если путь `MAIN_JSONL` НЕ содержит `$PROJECT_SLUG` — это чужой проект. Немедленно:
   - Выведи: `WARN: захвачен JSONL из чужого проекта ($MAIN_JSONL), ищу в project-dir...`
   - Повтори поиск явно в `$JSONL_DIR` и используй результат
   - Если `$JSONL_DIR` пуст — сообщи пользователю и останови

2. **Проверка сообщений:** если messages < 10 — вероятно не та сессия. Перебери топ-3 по mtime в project-dir:
```bash
ls -t "$JSONL_DIR"/*.jsonl 2>/dev/null | head -3
```
Выбери тот, у которого messages ≥ 10. Повтори архивацию с `--jsonl <правильный_путь>`.

3. **Проверка субагента:** если в `jsonl_path` из вывода скрипта содержится `/subagents/` — немедленно повтори поиск с явным исключением и сообщи пользователю о баге в `find_current_jsonl()`.

Если после архивации был ещё содержательный разговор, команду можно запустить повторно: запись с тем же `session_id` будет обновлена.
