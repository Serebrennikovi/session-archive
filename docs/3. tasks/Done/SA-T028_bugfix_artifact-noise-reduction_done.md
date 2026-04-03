**Дата:** 2026-04-03
**Выполнено:** 2026-04-03
**Статус:** done
**Спецификация:** —

# SA-T028 — Снизить шум в артефактах: ide_opened_file, Glob, skill-примеры, config-файлы

## Customer-facing инкремент

После архивирования сессии: в артефактах только реально изменённые или прочитанные в работе файлы; задачи — только те, с которыми реально работали; skill-теги — только использованные навыки, не прочитанные конфиги.

---

## Баги

### BUG-ARTIFACTS-IDE-OPEN-AS-READ — `ide_opened_file` создаёт артефакты типа "read"

**Симптом:** Когда пользователь открывает файл в IDE (VSCode подсвечивает файл), Claude Code добавляет в JSONL `<ide_opened_file>` тег. Скрипт интерпретирует это как Read tool call и добавляет файл в `session_artifacts` с action=`read`.

**Root cause:** `extract_artifacts()` парсит `ide_opened_file` теги наравне с реальными Read tool calls.

**Повторялось:** Зарегистрирован как open.

**Fix:**
```python
# В extract_artifacts() — игнорировать ide_opened_file как источник артефактов
# ide_opened_file — это UI hint, а не реальное чтение файла Claude

def extract_artifacts(messages, cwd):
    for msg in messages:
        # Пропустить ide_opened_file полностью
        if 'ide_opened_file' in (msg.get('metadata', {}) or {}):
            continue
        # Не парсить текст сообщений на предмет ide_opened_file тегов
        text = msg.get('text', '') or ''
        # Убрать <ide_opened_file>...</ide_opened_file> из текста перед парсингом
        text = re.sub(r'<ide_opened_file>.*?</ide_opened_file>', '', text, flags=re.DOTALL)
        # ... продолжение парсинга
```

---

### BUG-ARTIFACTS-GLOB-VS-READ — Glob tool создаёт артефакты типа "read"

**Симптом:** Вызов `Glob` tool (поиск файлов по паттерну) создаёт записи в `session_artifacts` для каждого найденного файла. Glob — это поиск, не чтение. Файл может быть в результатах Glob, но Claude его не читал.

**Root cause:** `extract_artifacts()` обрабатывает Glob tool results как Read.

**Повторялось:** Зарегистрирован как open.

**Fix:**
```python
# Tool allowlist для создания артефактов типа "read":
READ_TOOLS = {'Read', 'NotebookRead'}
# НЕ включать: 'Glob', 'Grep', 'LS', 'Find', 'Bash' (кроме cat/head/tail)

WRITE_TOOLS = {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}

def classify_tool_call(tool_name, tool_input, tool_result):
    if tool_name in READ_TOOLS:
        return 'read', tool_input.get('file_path')
    if tool_name in WRITE_TOOLS:
        return 'modified', tool_input.get('file_path') or tool_input.get('path')
    if tool_name == 'Bash':
        cmd = tool_input.get('command', '')
        # cat/head/tail → read (если один файл)
        m = re.match(r'(?:cat|head|tail)\s+(?:-[^\s]+\s+)?([^\s|]+)', cmd)
        if m and not m.group(1).startswith('-'):
            return 'read', m.group(1)
    return None, None  # Glob, Grep, LS — не создают артефакты
```

---

### BUG-TASKS-FALSE-POSITIVE-SKILL-EXAMPLE — task IDs из примеров в skill-контенте

**Симптом:** Task IDs из примеров внутри skill-промптов (например `T097`, `T123` в `/codereview` контенте) попадают в `session_tasks` как reviewed.

**Root cause:** `extract_task_ids()` работает по regex по всему тексту, включая инжектированные skill-промпты. Skill-промпт `/codereview` содержит примеры `T097`, `T123` как шаблонные IDs.

**Повторялось:** 2+ раза (019d4f8b, другие).

**Fix:**
```python
# Исключить skill-контент из поиска task IDs
# Skill-контент = текст между <command-message> и первым assistant-ответом

def find_skill_content_ranges(messages):
    """Вернуть list of (start_idx, end_idx) message ranges с skill-контентом."""
    ranges = []
    for i, msg in enumerate(messages):
        if msg.get('role') == 'user':
            text = msg.get('text', '') or ''
            if '<command-message>' in text or '<command-name>' in text:
                # Это сообщение — skill invocation, его контент не источник task IDs
                ranges.append(i)
    return set(ranges)

def extract_task_ids(messages):
    skill_messages = find_skill_content_ranges(messages)
    task_ids = set()
    for i, msg in enumerate(messages):
        if i in skill_messages:
            continue  # пропустить skill-промпт сообщения
        # ... обычный парсинг
```

---

### BUG-TAGS-SKILL-CONFIG-FILE — чтение `SKILL.md` создаёт skill-тег

**Симптом:** Когда Claude читает `SKILL.md` конфиг-файл (через Read tool в artifacts), это иногда приводит к добавлению skill-тега для этого скилла, даже если скилл реально не выполнялся.

**Root cause:** `detect_skills()` ищет skill-имена в прочитанных файлах. Файл `archive-session.md` содержит строку "archive-session" — и это создаёт тег.

**Повторялось:** Зарегистрирован как open.

**Fix:**
```python
# Skill-теги извлекать ТОЛЬКО из:
# 1. Skill tool calls: {"name": "Skill", "input": {"skill": "..."}}
# 2. command-name/command-message тегов из user-messages (SA-T024)
# НЕ из: содержимого прочитанных файлов, tool results, system-reminder

# Существующий detect_skills() уже должен делать это после SA-T012.
# Добавить явный тест: прочитанный SKILL.md НЕ создаёт skill-тег
```

---

### BUG-TASKS-ID-NO-PREFIX (open) — task IDs без project-prefix смешиваются

**Симптом:** Task `T015` из одного проекта и `ADV-T015` из другого парсятся вместе. Или `T015` из SessionArchive и `T015` из Cleaning-bot — одинаковые номера.

**Root cause:** `extract_task_ids()` возвращает только числовую часть, без project-prefix. В mixed-project сессиях или при чтении HANDOFF других проектов — смешивание.

**Повторялось:** Зарегистрирован как open.

**Fix:**
```python
# Добавить project-prefix detection:
# Если файл находится в cwd → prefix из cwd basename
# Если task упоминается в контексте конкретного project → его prefix
# Минимальный fix: требовать explicit prefix (SA-T, ADV-T) или фильтровать
# по cwd (только task-файлы в текущем проекте)

def normalize_task_id(raw_id, cwd):
    """Нормализовать task ID с проектным prefix."""
    known_prefixes = {
        '12_SessionArchive': 'SA',
        'autodev': 'ADV',
        'cleaning-bot': 'T',
    }
    project = os.path.basename(cwd)
    prefix = next((v for k, v in known_prefixes.items() if k in project), '')

    if re.match(r'^[A-Z]{2,5}-T\d+$', raw_id):
        return raw_id  # уже с prefix
    if re.match(r'^T\d+$', raw_id) and prefix:
        return f'{prefix}-{raw_id}'
    return raw_id
```

---

## Scope

- `extract_artifacts()`: исключить `ide_opened_file` как источник артефактов
- `extract_artifacts()`: Glob/Grep/LS не создают read-артефакты
- `extract_task_ids()`: пропускать skill-prompt сообщения (содержащие `<command-message>`)
- `detect_skills()`: убедиться что Read на SKILL.md не создаёт skill-тег (только tool calls)
- `normalize_task_id()`: добавить project-prefix нормализацию

## Out of scope

- Полный рефактор classifier (будет в SA-T029)
- Ретроактивное исправление старых записей

---

## Как протестировать

1. Сессия с открытым в IDE файлом → файл не появляется в session_artifacts как read
2. Glob("**/*.ts") → найденные файлы не в session_artifacts
3. Skill-промпт с `T097/T123` в примерах → эти IDs не в session_tasks
4. Read на `archive-session.md` → `skill:archive-session` не появляется без Skill tool call

## Критерии приёмки

1. `ide_opened_file` не создаёт артефакты
2. Glob tool results не в артефактах
3. Task IDs из skill-prompt примеров не в session_tasks
4. Чтение SKILL.md ≠ использование скилла
