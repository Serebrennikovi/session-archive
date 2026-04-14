**Дата:** 2026-04-09
**Статус:** open
**Severity:** HIGH

# SA-T073 — Кросс-сессионная контаминация при пустом --tool-ids

## Проблема

Когда `--tool-ids` пуст (или не передан), парсер обрабатывает **весь JSONL файл** без фильтрации по границам сессии. Один JSONL файл может содержать сообщения из нескольких последовательных чатов (Claude Code дописывает в тот же файл). Результат: архив одной сессии содержит артифакты, задачи, диффы и события из других сессий в том же файле.

## Отличие от SA-T071

SA-T071 — **неправильный JSONL** выбран (чужой файл). SA-T073 — **правильный JSONL**, но парсер не различает границы сессий внутри файла.

## Воспроизведение (2026-04-09, session e12a7106, sproektirui)

1. JSONL `e12a7106-8821-4a20-ad27-088b30755b9f.jsonl` содержит данные минимум 2-х чатов:
   - Предыдущий чат: T151 codereview (batch T151/T152/T153), eslint, визуальная проверка
   - Текущий чат: T152 codereview (только T152, только чтение файлов + запись ревью)

2. `/archive-session` запущен с `--tool-ids ''` (tool IDs из контекста были недоступны / не матчились)

3. Парсер обработал весь JSONL → результат содержал:
   - **Tasks:** T151, T152, T153 (вместо только T152)
   - **Events:** handoff_read, changelog_read, task_read, eslint_run (changelog_read и eslint_run — из T151 сессии)
   - **Artifacts:** SeriesReview.jsx, WindowVisualization.jsx, S15_sprint4.md, CHANGELOG.md (из T151 сессии)
   - **Diffs:** T151 task file edit (из T151 сессии)
   - **Summary:** описывало T151, не T152
   - **Skills:** codereview-local (из T151 сессии, в T152 использовался codereview)

4. Ручная верификация (`/verify-archive`) обнаружила все расхождения. Потребовалось:
   - 12+ Edit-операций на export .md файл (hook-скрипт постоянно перезаписывал правки)
   - Прямые SQL-запросы для исправления SQLite
   - Установка `manually_reviewed = 1` для защиты от перезаписи

## Корневая причина

`session_archive.py` при парсинге JSONL:
1. Не фильтрует сообщения по session boundary (нет session_id маркера в JSONL?)
2. При пустом `--tool-ids` обрабатывает 100% сообщений
3. Нет fallback-эвристики для определения начала текущей сессии

## Побочный эффект: hook перезаписывает ручные правки

При Edit export `.md` файла срабатывает hook (linter?), который перезапускает парсер и перезаписывает содержимое. Это делает ручное исправление архива крайне болезненным (каждый Edit откатывается). Только `manually_reviewed = 1` в SQLite останавливает перезапись.

## Рекомендации по фиксу

### Вариант 1: Session boundary detection в JSONL
Искать маркеры начала новой сессии в JSONL (например, системные сообщения с conversation_id, или паузы > N минут между сообщениями). Обрабатывать только последний блок.

### Вариант 2: Обязательный --tool-ids
Если `--tool-ids` пуст — выдавать WARNING и предлагать пользователю передать IDs. Не обрабатывать весь файл молча.

### Вариант 3: tool-ids из conversation context
Claude знает свои tool_call IDs. Шаблон `/archive-session` уже просит собрать их (Шаг 2). Проблема: при длинных сессиях или context compaction IDs могут быть недоступны. Нужен fallback.

### Вариант 4: Reverse parsing
Парсить JSONL с конца, останавливаясь на первом "user" message типа skill invocation (archive-session) или на маркере начала сессии. Это гарантирует захват только последней сессии.

## Масштаб проблемы

Любой проект с >1 чатом в истории подвержен этому багу. Чем активнее проект (больше сессий в JSONL), тем больше контаминация.

## Воспроизведение #2 (2026-04-09, session f8a14e62, sproektirui)

1. JSONL `f8a14e62-0fd0-4732-8c37-e721d8ae83ef.jsonl` содержит данные минимум 2-х чатов:
   - Предыдущий чат: T151 visualcheck (desktop+mobile, SeriesModal popup)
   - Текущий чат: T153 visualcheck (canvas визуализация места установки)

2. `/archive-session` запущен с `--summary "Visual check T153..."` и `--tool-ids ''`

3. Результат:
   - **Summary:** описывало T151, не T153 — `--summary` проигнорирован
   - **Tasks:** T042, T099, T151 (вместо T153) → после hook re-extract: T151
   - **Artifacts:** T151 скриншоты (t151-*.png вместо t153-*.png)
   - **Events:** только handoff_read, session_archived (не visualcheck, e2e_test)
   - **Diffs:** содержали T151, T152, T153 изменения (все uncommitted из git)

4. Причина игнорирования `--summary`: `summary_manual` в SQLite уже содержал T151 текст от предыдущего archive-current (SA-T072 воспроизведение). Скрипт не перезаписал его.

5. **Новый симптом:** hook на Edit tool перезаписывает export .md файл даже после `manually_reviewed = 1` в SQLite. `manually_reviewed` защищает SQLite row, но не export file.

6. Потребовалось: Python-скрипт (Bash tool) для обхода hook при правке export файла.

## Воспроизведение #3 (2026-04-09, session c3b5fb9d, sproektirui)

1. JSONL `c3b5fb9d-7359-4e97-a476-3c7f9b9df217.jsonl` содержит данные T153 codereview-free + fix сессии.
2. `/archive-session` запущен из ДРУГОЙ сессии (T152, session `8f1a8c41`), но `ls -t` выбрал `c3b5fb9d` как самый свежий JSONL.
3. Tool-IDs недоступны (post-context-compaction fallback).
4. Результат: архив `c3b5fb9d` содержит полные данные T153 (summary, tasks, artifacts, diffs, transcript), а T152 сессия осталась без архива.
5. **Комбинация SA-T071 + SA-T073:** неправильный JSONL (T071) + весь JSONL обработан без фильтрации (T073).
6. **Fix:** Re-archived T152 с корректным JSONL `8f1a8c41`. Оставил `c3b5fb9d` как-is (содержит корректные данные T153).

## Воспроизведение #4 (2026-04-11→12, session fa809fcb, autodev-v2)

1. JSONL `fa809fcb-97d8-4a6f-94d2-8b70ac8beae5.jsonl` содержит данные минимум 2-х чатов:
   - Предыдущий чат: `/fix T034` (R1, R2 HIGH закрыты, CLI smoke)
   - Текущий чат: `/intro` + анализ багов T045/T034 + `/fix T045` (N11 shared build, N1 timeout bump)

2. `/archive-session` запущен с `--summary "Загрузка контекста AutoDev v2, анализ багов..."` и `--tool-ids ''`

3. Результат:
   - **Summary:** описывало T034, не T045 — `--summary` аргумент проигнорирован (скрипт использовал auto-generated summary из JSONL, которая описывала предыдущую сессию)
   - **Tasks:** `ADV-T045, T042` (T042 — phantom из предыдущей сес��ии, не упоминался в текущей)
   - **Artifacts:** 9 файлов (modified), из которых 5 — из предыдущей T034 сессии (plan_spec_critic.md, main.go, plan_test.go, findings_test.go, writer.go)
   - **Diffs:** 8 diff-блоков, из которых 6 — из предыдущей T034 сессии

4. `/verify-archive` обнаружил все расхождения. Исправлено:
   - Summary → ручной override в export .md и SQLite
   - Tasks: удалён T042, добавлен ADV-T034 (read)
   - Artifacts: удалены 5 phantom файлов, T034 doc переведён в action=read
   - Diffs: удалены 6 foreign diff-блоков (519 строк)

5. **Тот же паттерн что #1–#3:** без --tool-ids парсер обрабатывает весь JSONL и summary/tasks/artifacts/diffs загрязняются из предыдущей сесси��.

## Воспроизведение #5 (2026-04-12, session 591c2ded, autodev-v2)

1. JSONL `591c2ded-a315-470c-9d09-c5fb68287ed6.jsonl` содержит данные минимум 2-х чатов:
   - Предыдущий чат: T034 code review + smoke + fix (critic.go, writer.go, main.go)
   - Текущий чат: T045 `/codereview` (integration tests, только чтение + 1 append в task file)

2. `/archive-session` запущен с `--tool-ids ''` (длинная сессия, IDs недоступны)

3. Результат:
   - **Tasks:** ADV-T034, SA-T077, SA-T078, T034, T042 (вместо только ADV-T045)
   - **Artifacts:** 11 файлов, из которых 8 — из предыдущей T034 сессии (plan_spec_critic.md, main.go, writer.go, parser.go, critic.go, findings_test.go, plan_test.go, HANDOFF.md)
   - **Diffs:** 930 строк из 7 файлов — ВСЕ из предыдущей T034 сессии. Реальный diff (T045 task file append) был включён, но смешан с чужими
   - **Tags:** `skill: fix` (от предыдущей сессии) вместо `skill: codereview`
   - **Transcript:** содержит сообщения из предыдущей T034 сессии (первое сообщение: `t034 /fix`)

4. `/verify-archive` обнаружил все расхождения. Исправлено:
   - Tasks: заменены на ADV-T045
   - Tags: skill:fix → skill:codereview
   - Artifacts: удалены 8 phantom, оставлены 7 реальных (1 modified + 6 read)
   - Diffs: удалены 930 строк foreign diffs, заменены на session-scoped описание
   - SQLite: все таблицы (tags, tasks, events, artifacts) обновлены, `manually_reviewed = 1`

5. **Тот же паттерн что #1–#4:** без --tool-ids парсер обрабатывает весь JSONL. Summary корректен (передан через --summary), но tasks/artifacts/diffs/tags загрязнены из предыдущей сессии.

## Воспроизведение #6 (2026-04-12, session 7eea8025, autodev-v2)

1. JSONL содержит данные минимум 2-х чатов:
   - Предыдущий чат: `/codereview T045` (integration tests review, только чтение + 1 append)
   - Текущий чат: `/codereview T034` (spec critic findings review, чтение + 3 append)

2. `/archive-session` запущен с `--tool-ids ''` (IDs недоступны после context compaction)

3. Результат:
   - **Tasks:** ADV-T045 (phantom из предыдущей T045 сессии) — вместо только ADV-T034
   - **Events:** phantom events из предыдущей сессии
   - **Artifacts:** 5 файлов с action=`modified` из git_head вместо `read` (SA-T075/SA-T076 overlap)
   - **Diffs:** 7 phantom diff-блоков (~600 строк) из T045/T034 prior sessions

4. `/verify-archive` обнаружил все расхождения. Исправлено:
   - Tasks: заменены на ADV-T034
   - Events: исправлены
   - Tags: domain `planning` → `spec_hardening`
   - Artifacts: 5 phantom `modified` → `read`, добавлен HANDOFF как `read`
   - Diffs: удалены 7 phantom diff-блоков, оставлен только T034 task file diff
   - SQLite: все таблицы обновлены, `manually_reviewed = 1`

5. **Тот же паттерн что #1–#5:** без --tool-ids парсер обрабатывает весь JSONL. Summary корректен (передан через --summary), но tasks/artifacts/diffs загрязнены из предыдущей сессии.

## Воспроизведение #7 (2026-04-12, session 4065ce28, autodev-v2)

1. Сессия: ревью gate-tasks T055/T056, создание coverage таблиц, добавление тестов, сохранение gate-task mental model в memory. `/archive-session` запущен в конце.

2. Последующая сессия (T057 — extract finalize methods) запустила `/archive-session` из того же JSONL → **перезаписала** export `.md` и SQLite record для `4065ce28`.

3. Результат: export содержит данные T057, не T055/T056 review:
   - **Summary:** "Создана задача ADV-T057..." (вместо review T055/T056)
   - **Tasks:** ADV-T057 (вместо ADV-T055, ADV-T056)
   - **Artifacts:** 3 файла T057 (вместо ~15 файлов T055/T056 review)
   - **Tool calls:** 9 (вместо ~50+)

4. **Новый симптом:** не контаминация внутри одной записи, а **полная перезапись** предыдущей записи последующей сессией. JSONL filename = session_id → обе сессии получают один session_id → вторая перезаписывает первую.

5. `/verify-archive` обнаружил полную подмену. Исправление невозможно без tool-ids (context compacted, IDs недоступны). Данные первой сессии потеряны.

6. **Рекомендация:** session_id должен быть уникальным per-conversation, а не per-JSONL-file. Либо архиватор должен отказываться перезаписывать `manually_reviewed = 1` записи.

## Воспроизведение #8 (2026-04-13, session 10088ba3, autodev-v2)

1. Сессия: gate review T031 (S05 integration tests). /intro → обсуждение гейт-тасок → создание промпта ревью → gate review → /fix T031 text → /archive-session.

2. JSONL `10088ba3-af21-4d69-87fa-6a2c316196ea.jsonl` содержит данные минимум 2-х чатов:
   - Предыдущий чат: `/fix T026` (14 findings, правка .go файлов: task_dag_scheduler.go, task_worker.go, state.go, run.go)
   - Текущий чат: gate review T031 (только чтение спек/тасок + Edit двух .md файлов)

3. `/archive-session` запущен с `--tool-ids ''` (tool IDs недоступны)

4. Результат:
   - **Transcript:** полностью из предыдущей T026 /fix сессии (первое сообщение: "t026 /fix", план из 14 FIX-ов)
   - **Tasks:** T026, T042 (вместо T031, T045, T055, T056)
   - **Artifacts:** 8 файлов, из которых 4 (.go файлы) — из T026 fix сессии
   - **Diffs:** 5 блоков, из которых 3 (.go diffs ~230 строк) — из T026 session
   - **Tags:** `skill: fix` (вместо `codereview, fix`)
   - **Events:** `spec_read` (неполные — пропущены handoff_read, architecture_read, task_review)
   - **Summary:** корректен (передан через --summary)

5. `/verify-archive` обнаружил все расхождения. Исправлено:
   - Transcript: заменён на summary реальных шагов сессии (T026 transcript удалён)
   - Tasks: T026,T042 → T031,T045,T055,T056
   - Tags: skill:fix → skill:codereview,fix; domain:backend → domain:backend,docs
   - Events: добавлены handoff_read, architecture_read, task_review
   - Artifacts: удалены 4 phantom .go файла, добавлены 4 реально читанных .md файла
   - Diffs: удалены 3 foreign .go diff-блока (~210 строк), оставлены T031.md и HANDOFF.md

6. **Тот же паттерн что #1–#7:** без --tool-ids парсер обрабатывает весь JSONL. Summary корректен (--summary override), но transcript/tasks/artifacts/diffs загрязнены из предыдущей сессии.

## Связанные баги

- SA-T071 (wrong JSONL selection) — другой баг, но часто проявляется вместе
- SA-T072 (rerun overwrites summary) — `manually_reviewed` guard был добавлен как workaround для перезаписи
- SA-T052 (phantom diffs) — контаминация из git status, здесь — из другой сессии в том же JSONL
- SA-T075 (diffs from uncommitted prior sessions) — git_head diffs include all uncommitted changes
