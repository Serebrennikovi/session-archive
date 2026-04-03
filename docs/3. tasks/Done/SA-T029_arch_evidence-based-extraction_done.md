**Дата:** 2026-04-03
**Статус:** done 2026-04-03
**Спецификация:** —

# SA-T029 — Архитектура: Evidence-based extraction layer

## Customer-facing инкремент

Все поля архивной записи (теги, задачи, события, артефакты, summary) строятся из верифицируемых tool calls, а не из текстовых эвристик. Ручные правки через `/verify-archive` становятся редкостью.

---

## Проблема

Текущая архитектура `session_archive.py` — **text-heuristic first**:
- domain-теги определяются по ключевым словам в тексте диалога
- events детектируются regex по assistant/user тексту ("задеплоили", "запустили тесты")
- task IDs ищутся по всему JSONL включая skill-промпты и tool results
- artifacts собираются из смеси Read/Write/Edit calls + text mentions

**Результат:** каждая сессия требует 5-15 ручных правок через `/verify-archive`.

---

## Архитектурное решение: Evidence Accumulator

### Концепция

Ввести слой `EvidenceAccumulator` — структуру, которая накапливает только **подтверждённые** факты из tool calls:

```
JSONL messages
    ↓
[EvidenceAccumulator]  ← единственный источник правды
    ↓
{
  tool_calls: [{name, input, result, is_error}],   ← все вызовы
  reads: [{path, content_preview}],                 ← только Read/cat tool calls
  writes: [{path, old_size, new_size}],             ← Edit/Write/MultiEdit
  bashes: [{cmd, exit_code, stdout_preview}],       ← Bash calls
  skill_calls: [{skill_name, args}],                ← Skill tool calls
  command_tags: [{skill_name, source}],             ← <command-name> tags
  task_file_edits: [{task_id, path, action}],       ← задачи с реальным Edit
  archive_boundary: int,                            ← индекс archive-current вызова
}
    ↓
Derivers (строят metadata из Evidence):
  derive_artifacts(evidence) → session_artifacts
  derive_tasks(evidence) → session_tasks
  derive_events(evidence) → session_events
  derive_tags(evidence) → session_tags
  derive_summary(evidence, messages) → summary
```

### Ключевые правила деривации

**Артефакты:**
```python
def derive_artifacts(evidence):
    artifacts = []
    # ТОЛЬКО из подтверждённых tool calls:
    for w in evidence.writes:
        artifacts.append({path: w.path, action: classify_write(w)})
    for bash in evidence.bashes:
        artifacts.extend(parse_bash_artifacts(bash))  # mv/cp/rm
    # Read — только если не Glob/Grep, не ide_opened_file, не after archive_boundary
    for r in evidence.reads:
        if r.source_tool in ('Read', 'NotebookRead'):
            artifacts.append({path: r.path, action: 'read'})
    return filter_by_cwd(artifacts, evidence.cwd)
```

**Задачи:**
```python
def derive_tasks(evidence):
    tasks = set()
    # Только из Write/Edit на task-файлы
    for edit in evidence.task_file_edits:
        tasks.add(edit.task_id)
    # + из Bash mv/cp на task-файлы (SA-T027)
    for bash in evidence.bashes:
        tasks.update(extract_task_ids_from_bash(bash.cmd))
    # НЕ из: прочитанных HANDOFF, skill-промптов, tool results
    return tasks
```

**События:**
```python
def derive_events(evidence):
    events = []
    # deploy → только если Bash содержит ssh/docker push/gh workflow
    if any(is_deploy_cmd(b.cmd) for b in evidence.bashes):
        events.append('deploy')
    # tests_run → только если pytest/npm test завершился с exit_code=0
    if any(is_test_cmd(b.cmd) and b.exit_code == 0 for b in evidence.bashes):
        events.append('tests_run')
    # commit_made → только если git commit успешен
    if any('git commit' in b.cmd and b.exit_code == 0 for b in evidence.bashes):
        events.append('commit_made')
    # session_archived → только если archive-current tool call был
    if evidence.archive_boundary < len(evidence.tool_calls):
        events.append('session_archived')
    return events
```

**Domain-теги:**
```python
def derive_domain_tags(evidence):
    domains = set()
    all_paths = [a.path for a in evidence.writes + evidence.reads]
    # Только по расширениям реально изменённых файлов
    if any(p.endswith(('.tsx', '.jsx', '.vue', '.css', '.html')) for p in all_paths):
        domains.add('frontend')
    if any(p.endswith(('.py', '.go', '.rs', '.java')) for p in all_paths):
        domains.add('backend')
    if any(p.endswith(('.sql',)) or 'migration' in p for p in all_paths):
        domains.add('database')
    if any(p.endswith('.sh') for p in all_paths) or evidence.bashes:
        domains.add('shell')
    return domains
```

---

## Покрываемые баги

| Баг | Как покрывается |
|-----|----------------|
| BUG-TAGS-DOMAIN-DATABASE-FALSE (open) | derive_domain_tags() по file extensions only |
| BUG-EVENTS-FALSE-POSITIVE (recurring) | derive_events() по tool call exit codes |
| BUG-PARALLEL-SESSION-OVERWRITE (open) | archive_boundary isolates current session |
| BUG-DIFF-PARALLEL-SESSION (open) | filter_by_cwd() + archive_boundary |
| BUG-ARTIFACTS-GLOB-VS-READ | classify_tool_reads() исключает Glob |
| BUG-ARTIFACTS-IDE-OPEN-AS-READ | filter ide_opened_file из evidence |
| BUG-TASKS-FALSE-POSITIVE-SKILL-EXAMPLE | tasks only from task_file_edits |
| BUG-SUMMARY-CONTEXT-DRIFT | summary from evidence.task_file_edits |

---

## Параллельные сессии (BUG-PARALLEL-SESSION-OVERWRITE, BUG-DIFF-PARALLEL-SESSION)

**Проблема:** Два экземпляра Claude Code в одном проекте → два JSONL в одной директории → архивация может захватить tool calls из параллельной сессии.

**Решение:**
```python
# В EvidenceAccumulator: фильтровать по session_id из JSONL
# Каждое JSONL-сообщение содержит session_id в metadata
# Если session_id не совпадает с target_session_id — пропустить

def accumulate(jsonl_path, target_session_id):
    with open(jsonl_path) as f:
        for line in f:
            msg = json.loads(line)
            if msg.get('session_id') != target_session_id:
                continue  # параллельная сессия
            evidence.add(msg)
```

---

## Scope

- Создать класс `EvidenceAccumulator` в `session_archive.py`
- Реализовать `derive_artifacts()`, `derive_tasks()`, `derive_events()`, `derive_domain_tags()`
- Обновить `derive_summary()` для использования evidence.task_file_edits
- Добавить `archive_boundary` detection
- Добавить session_id фильтрацию в парсере JSONL
- Перенести существующие extractors на EvidenceAccumulator поэтапно (не breaking change)

## Out of scope

- Полный рефактор UI/export
- Ретроактивная перегенерация старых записей
- Изменение SQLite-схемы (только поведение экстракторов)

## Порядок реализации (предлагаемый)

1. Создать `EvidenceAccumulator` как dataclass, populate из JSONL-парсера
2. Реализовать `derive_domain_tags()` — минимальный риск
3. Реализовать `derive_events()` — заменяет регрессионный BUG-31
4. Реализовать `derive_tasks()` — заменяет BUG-TASKS-*
5. Реализовать `derive_artifacts()` — наибольший объём
6. Feature flag: `--evidence-layer` для поэтапного тестирования

---

## Как протестировать

1. Запустить archive на сессию с BUG-TAGS-DOMAIN-DATABASE-FALSE → только реальные domains
2. Запустить archive на сессию с `deploy` только упомянутым (не выполненным) → deploy не в events
3. Две параллельные сессии → каждая архивирует только свои артефакты

## Критерии приёмки

1. domain-теги = только по расширениям реально изменённых файлов (не по тексту)
2. events = только по exit code 0 / реальным tool calls (не по тексту)
3. tasks = только из task_file_edits (не из упоминаний в prose)
4. Параллельная сессия не попадает в артефакты другой
5. Количество обязательных ручных правок в verify-archive: ≤ 2 на сессию (цель)
