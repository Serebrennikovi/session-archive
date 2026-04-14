**Дата:** 2026-04-07
**Статус:** open
**Severity:** MEDIUM

# SA-T049 — Task IDs дублируются и включают false positives

## Проблема

Парсер извлекает task IDs из текста сообщений без дедупликации и без проверки контекста. Результат:

1. **Дубли:** `ADV-T023` и `T023` записываются как две разные задачи (46 записей вместо 26)
2. **False positives:** Задачи упомянутые в прочитанных файлах (HANDOFF, specs) попадают в список, даже если сессия их не трогала. Пример: T040 listed as modified, но не входил ни в один батч правок.
3. **Artifacts false positives:** `docs/ADV-HANDOFF.md` listed as modified — не модифицировался в сессии, только читался парсером из контекста.

### Новое воспроизведение (2026-04-07, session e892faa8)

Фантом `T042` в Tasks — сессия работала ТОЛЬКО с T023, но T042 упоминается в прочитанных HANDOFF/спеках (S08 task table). Парсер извлёк T042 из tool_result контекста без фильтрации Read vs Edit.

### Новое воспроизведение (2026-04-07, session 24fa7545)

Фантомы `T001`, `T042`, дубликат `T024` (при наличии `ADV-T024`). Сессия выполняла smoke test только ADV-T024. T001/T042 извлечены из HANDOFF-контента (Read tool result). T024 — дубликат без префикса ADV-. Паттерн идентичен e892faa8.

### Новое воспроизведение (2026-04-08, session d62bc616)

Сессия: smoke test ADV-T048 (autodev-v2). Парсер записал 5 task IDs:
- `ADV-T048` (smoketested) — корректно ✅
- `T048` — дубликат `ADV-T048` ❌
- `T001` — из mock test data в engine_test.go (`newTask()` returns TaskID "ADV-T001"), прочитан через Read tool ❌
- `T024` — из diffs/specs (referenced as dependency), не работали с задачей ❌
- `T042` — из текста промпта `/smoketest` (пример формата: "T042, t042, 042") ❌

Паттерн идентичен 24fa7545 и a8633fe2: парсер не фильтрует Read tool results и prompt templates.

### Новое воспроизведение (2026-04-07, session a8633fe2)

Сессия: code review ADV-T024 (autodev-v2). Парсер записал 4 task IDs:
- `ADV-T024` (reviewed) — корректно ✅
- `T024` (reviewed) — дубликат `ADV-T024` ❌
- `T042` (mentioned) — ложный позитив из текста промпта `/codereview` (пример формата: "T042, t042, 042") ❌
- `T099` (implemented!) — ложный позитив из текста промпта `/codereview` (пример: "T099, JIRA-123"). Классифицирован как `implemented` — парсер не отличает текст промпта от реального кода ❌

**Новый root cause:** skill prompt templates (`/codereview`) содержат task ID примеры в тексте инструкций. Парсер не фильтрует Skill-expanded текст. Любой TNN паттерн в промпте считается задачей.

**Дополнительный баг:** `T099` classified as `implemented` хотя задача не существует — action assigned без валидации.

### Новое воспроизведение (2026-04-07, session 58fb4abd)

Сессия: smoke test R2 для ADV-T024 (autodev-v2). Парсер записал 4 task IDs:
- `ADV-T024` (reviewed) — корректно ✅
- `T024` (reviewed) — дубликат `ADV-T024` ❌
- `T001` (implemented!) — ложный позитив из текста промпта `/smoketest` (skill template содержит примеры: "adv run", "task T001 started") ❌
- `T042` (mentioned) — ложный позитив из текста промпта `/smoketest` (примеры: "T042, t042, 042" в инструкции по разбору task ID) ❌

**Root cause:** идентичен session a8633fe2 — skill prompt templates содержат task ID примеры. Парсер не фильтрует Skill-expanded text.

### Новое воспроизведение (2026-04-08, session e78a1b60)

Сессия: code review ADV-T032 (autodev-v2). Парсер записал 6 task IDs:
- `ADV-T032` (reviewed) — корректно ✅
- `T032` (reviewed) — дубликат `ADV-T032` ❌
- `T001` (implemented!) — false positive из HANDOFF content (Read tool result) ❌
- `T024` (mentioned) — false positive из HANDOFF/CHANGELOG context ❌
- `T042` (mentioned) — false positive из `/codereview` prompt template examples ❌
- `T048` (mentioned) — false positive из HANDOFF/CHANGELOG context ❌

**Root cause:** комбинация двух паттернов: (1) skill prompt templates с примерами task IDs, (2) Read tool results из HANDOFF/CHANGELOG содержат task IDs других задач.

### Новое воспроизведение (2026-04-08, session 1b9bfce0)

Сессия: независимый код-ревью ADV-T032 (autodev-v2). Парсер записал 3 task IDs:
- `ADV-T032` (reviewed) — корректно ✅
- `T032` (reviewed) — дубликат `ADV-T032` ❌
- `T042` (mentioned) — false positive из `/fix` skill prompt template (пример: `T{ID}`, `T042` в `path/file.py:42`) и HANDOFF content (S08 task table) ❌

**Root cause:** идентичен предыдущим воспроизведениям: (1) дедуп ADV-prefix, (2) skill prompt templates, (3) HANDOFF Read results.

### Новое воспроизведение (2026-04-08, session 2c2aa57e)

Сессия: независимый код-ревью ADV-T032 через `/codereview-free` + `/fix` + `/archive-session` (autodev-v2). Парсер изначально записал task IDs (исправлено скриптом до verify-archive):
- `ADV-T032` (reviewed) — корректно ✅
- `T032` — дубликат `ADV-T032` ❌ (удалён парсером до момента verify)
- `T042` — false positive из `/fix` skill prompt template (пример: `T{ID}`) и HANDOFF Read results ❌ (удалён)
- `T099` — false positive из `/fix` prompt template (пример: `T099, JIRA-123`) ❌ (удалён)

**Root cause:** идентичен: skill prompt templates + HANDOFF Read results. Примечание: в этом случае парсер сам выполнил частичную дедупликацию (убрал T032), но не убрал T042/T099. Финальная коррекция — парсер или автоматический cleanup между archive и export.

### Новое воспроизведение (2026-04-08, session 336dd55e)

Сессия: независимый код-ревью T032 через `/codereview-free` + `/fix` + обновление промптов `/codereview` и `/smoketest` (autodev-v2). Парсер записал 3 task IDs:
- `ADV-T032` (reviewed) — корректно ✅
- `T032` (reviewed) — дубликат `ADV-T032` ❌
- `T042` (mentioned) — false positive из HANDOFF Read results (S08 task table) ❌

**Дополнительный баг (skill tags):** парсер записал `skill: codereview` и `skill: smoketest` — оба НЕ вызывались в сессии. `/codereview` не запускался (запускался `/codereview-free`). `/smoketest` не запускался (только РЕДАКТИРОВАЛСЯ файл промпта smoketest.md). Парсер видимо совпал по тексту обсуждения этих скиллов.

**Root cause:** идентичен предыдущим: (1) дедуп ADV-prefix, (2) HANDOFF Read results, (3) text-match skill detection даёт false positives на упоминания скиллов в контексте.

### Новое воспроизведение (2026-04-09, session 947a5082)

Сессия: `/codereview-free` + `/fix` + `/accept` + `/archive-session` для ADV-T049 (autodev-v2). Парсер записал 3 task IDs:
- `ADV-T049` (reviewed) — корректно ✅
- `T049` (reviewed) — дубликат `ADV-T049` ❌
- `T042` (mentioned) — false positive из HANDOFF Read (S08 task table) ❌

Root cause идентичен: ADV-prefix dedup не работает, T042 из HANDOFF Read results. Вручную исправлено через SQLite и export .md.

### Новое воспроизведение (2026-04-12, session 9925b288)

Сессия: `/fix T045` + `/accept T045` + `/archive-session` (autodev-v2). Парсер записал 3 task IDs:
- `ADV-T045` (fixed, accepted) — корректно ✅
- `T042` — false positive из HANDOFF Read (S08 task table row) ❌
- `T045` — дубликат `ADV-T045` ❌

Root cause идентичен: парсер извлекает TNN паттерны из Read tool results без фильтрации. Вручную исправлено в export .md.

### Новое воспроизведение (2026-04-12, session 4e419074)

Сессия: review + fix ADV-T057 (autodev-v2). Парсер записал 2 task IDs:
- `ADV-T057` — корректно ✅
- `T057` — дубликат `ADV-T057` ❌

Root cause: ADV-prefix dedup всё ещё не работает. Вручную удалён `T057` из SQLite и export.

### Новое воспроизведение (2026-04-14, session 21dee077)

Сессия: code review #2 + fix ADV-T036 (autodev-v2). Парсер записал 3 task IDs:
- `ADV-T036` — корректно ✅
- `T036` — дубликат `ADV-T036` ❌
- `T042` — ложный позитив из git status (файл `ADV-T042_s08_plan_run_orchestrator.md` в uncommitted changes, не трогался в сессии) ❌

Root cause: ADV-prefix dedup всё ещё не работает + парсер извлекает task IDs из git status artifact paths. Вручную удалены `T036` и `T042` из SQLite и export.

## Рекомендация по фиксу

1. **Dedup:** нормализовать все task IDs к одному формату (`ADV-TННН`) перед записью
2. **Context filter:** различать "task mentioned in Read" vs "task modified by Edit/Write" — только последние записывать как Tasks
3. **Artifact filter:** отличать Read (input) от Edit/Write (output) — Read-only файлы не помечать как "modified"
