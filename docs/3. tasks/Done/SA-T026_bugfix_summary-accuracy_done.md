**Дата:** 2026-04-03
**Статус:** done 2026-04-03
**Спецификация:** —

# SA-T026 — Исправить точность Summary: context drift + mixed phases + partial

## Customer-facing инкремент

После архивирования сессии поле Summary точно описывает выполненную работу — не промежуточное состояние, не чужую задачу из HANDOFF/intro, не склейку нескольких фаз сессии.

---

## Баги

### BUG-SUMMARY-MISMATCH — summary описывает мини-действие, а не всю JSONL-сессию

**Симптом:** В сессии `37d18440` — `/archive-session` запускался повторно после дополнительного mcp permission fix. Summary оказался написан про это mcp-действие, а не про основную T288-работу из JSONL.

**Root cause:** `build_summary()` берёт "последнее substantive assistant message" из JSONL. Если после основной работы произошли дополнительные действия (permission fix, verify-archive), последнее сообщение описывает их, а не всю сессию.

**Повторялось:** 1+ раз.

**Fix:**
```python
def build_summary(messages, artifacts, task_ids):
    """
    Приоритеты для summary:
    1. --summary флаг (уже реализовано, sessions.summary_manual = 1)
    2. Последнее assistant-сообщение, которое упоминает реально изменённые task-файлы
    3. Если нет task-файлов — первое длинное assistant-сообщение (>200 символов) после
       последнего tool_call (не последнее в диалоге)
    4. Fallback: первые 300 символов последнего длинного assistant-сообщения
    """
    # Собрать пути task-файлов из artifacts
    task_file_paths = {a['file_path'] for a in artifacts
                       if re.search(r'[/\\]T\d+', a.get('file_path', ''))}

    # Найти assistant-сообщения, упоминающие task-файлы
    candidates = []
    for msg in messages:
        if msg.get('role') != 'assistant':
            continue
        text = msg.get('text', '') or ''
        if len(text) < 100:
            continue
        # Приоритет: сообщение упоминает task IDs или task file names
        score = sum(1 for t in task_ids if t in text)
        score += sum(1 for p in task_file_paths if os.path.basename(p) in text)
        candidates.append((score, len(text), text))

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return candidates[0][2][:500]

    # Fallback
    long_messages = [m for m in messages
                     if m.get('role') == 'assistant' and len(m.get('text', '') or '') > 200]
    if long_messages:
        return long_messages[-1]['text'][:500]
    return ''
```

---

### BUG-SUMMARY-CONTEXT-DRIFT — summary тащит referenced-only задачи

**Симптом:** В сессии `019d51d4` summary описывал `T139/T140/T141` как полноценные рабочие задачи, хотя они только упоминались в HANDOFF. В сессии `019d4f8b` summary включал `References: tasks T097, T123` из примеров в skill-контенте.

**Root cause:** `extract_task_ids()` работает по regex по всему тексту JSONL, включая: прочитанный HANDOFF, intro-summary, примеры из task-файлов, tool results.

**Повторялось:** 4+ раз.

**Fix:** Task IDs для summary должны приходить только из задач, с которыми реально работали:
```python
def extract_active_task_ids(messages, artifacts):
    """
    Задача считается активной если:
    1. Её файл (T\d+*.md) был изменён через Edit/Write/MultiEdit
    2. Или её ID явно фигурирует в Bash-командах (mv, sed) с путём task-файла
    НЕ считается: упоминание в тексте, Read tool без Edit, tool_results
    """
    active = set()
    for msg in messages:
        for tc in msg.get('tool_calls', []):
            name = tc.get('name', '')
            inp = tc.get('input', {})
            if name in ('Edit', 'Write', 'MultiEdit'):
                path = inp.get('file_path', '') or inp.get('path', '')
                m = re.search(r'[/\\](T\d+)', path)
                if m:
                    active.add(m.group(1))
    # Дополнить из artifacts (action=modified/created)
    for a in artifacts:
        if a.get('action') in ('modified', 'created'):
            m = re.search(r'[/\\](T\d+)', a.get('file_path', ''))
            if m:
                active.add(m.group(1))
    return active
```

---

### BUG-SUMMARY-MIXED-PHASES — summary склеивает разные фазы сессии

**Симптом:** В сессии `019d4f8b` summary склеился из позднего fix-ответа и раннего `$codereview`-запроса — включил ложные References, обрезанный Outcome, вынес resolved verification в Open issues.

**Root cause:** `build_summary()` не знает о структуре сессии (какая фаза была основной). Берёт последний длинный текст, который может быть финальным подтверждением verify-archive.

**Повторялось:** 1+ раз.

**Fix:** Исключить из кандидатов для summary сообщения после archive-session вызова:
```python
def find_archive_boundary(messages):
    """Найти индекс последнего archive-current tool call."""
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        for tc in msg.get('tool_calls', []):
            if 'archive' in tc.get('name', '').lower():
                return i
            inp = tc.get('input', {})
            cmd = inp.get('command', '')
            if 'archive-current' in cmd or 'archive_current' in cmd:
                return i
    return len(messages)  # no boundary found

# В build_summary — использовать только сообщения ДО archive_boundary
boundary = find_archive_boundary(messages)
relevant_messages = messages[:boundary]
```

---

### BUG-SUMMARY-PARTIAL (open) — summary обрывается на промежуточном состоянии

**Симптом:** Open: summary содержит "нужно получить точные значения от GitHub", хотя позднее SHA совпали и задача завершена.

**Root cause:** Summary строится из промежуточного assistant-сообщения, не из финального.

**Повторялось:** Зарегистрирован как open bug.

**Fix:** Покрывается `find_archive_boundary()` выше — summary строится из последнего крупного assistant-сообщения до начала archive-фазы.

---

## Scope

- Добавить `find_archive_boundary()` — определять границу до archive-current вызова
- Обновить `build_summary()`: кандидаты только до archive-boundary, приоритет по task-файлам
- Обновить `extract_task_ids()` для summary: только активные задачи (Edit/Write on task files)
- Summary для verify-archive фазы — не включать в candidates

## Out of scope

- Изменение формата summary в SQLite
- Автоматическая регенерация summary для старых записей

---

## Как протестировать

1. Сессия с `/intro` + `codereview T145` + дополнительным verify-archive
2. Проверить что summary описывает `codereview T145`, а не verify-archive
3. Task IDs в summary: только T145, не T097/T123 из примеров

## Критерии приёмки

1. Summary описывает основную фазу сессии, не verify-archive/mcp-fix хвост
2. Task IDs в summary = только задачи с реальными Edit/Write в сессии
3. Summary не содержит "нужно сделать X" если X уже выполнено до конца сессии
