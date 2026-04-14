**Дата:** 2026-04-09
**Статус:** open
**Severity:** HIGH

# SA-T071 — archive-session берёт чужой JSONL при параллельных чатах

## Проблема

Когда в одном проекте одновременно открыто несколько чатов Claude Code (VSCode), команда `/archive-session` использует `ls -t *.jsonl | head -1` для поиска «текущего» JSONL. Это выбирает самый свежий по mtime файл, который может принадлежать **другому чату**.

## Воспроизведение (2026-04-09, 3 параллельных чата в sproektirui)

1. Чат A (session `ac5135f6`) — T148 codereview
2. Чат B (session `fb6419f7`) — T149 codereview
3. Чат C (session `1dbec8ba`) — T148 visual check

Чат A выполнил `/archive-session`. В момент запуска `fb6419f7` был newest по mtime → архив записан в **чужой** session_id. Затем Чат B выполнил свой `/archive-session` и перезаписал экспорт `fb6419f7` корректными данными T149. Архив Чата A потерян, пришлось перезаписывать с `--jsonl <правильный_путь>`.

## Корневая причина

Скрипт `archive-session` (и шаблон skill'а) определяет JSONL через:
```bash
MAIN_JSONL=$(ls -t "$JSONL_DIR"/*.jsonl 2>/dev/null | head -1)
```
Это не учитывает, что у каждого чата свой JSONL. Правильный session_id доступен из контекста чата (например, из temp path `$TMPDIR/claude-*/...$SESSION_ID.../tasks/`).

## Побочные эффекты

- **Phantom artifacts/diffs** — при capture чужого JSONL парсер захватывает артифакты и диффы чужой сессии (SA-T052, SA-T060 рецидив)
- **Tool calls = 0/1** — `--tool-ids` не матчит tool calls в чужом JSONL
- **Перезапись** — второй archive-session в правильный JSONL уничтожает первый ошибочный архив

## Рекомендация по фиксу

**Вариант 1 (skill template):** в шаблоне `/archive-session` добавить шаг определения session_id из conversation context. Claude знает свой session_id — он виден в путях background tasks:
```
/private/tmp/claude-501/.../SESSION_ID/tasks/...
```

**Вариант 2 (script):** передавать `--session-id` явно. Скрипт должен сверять session_id из `--jsonl` с переданным `--session-id`.

**Вариант 3 (heuristic):** сравнить `--tool-ids` с tool_use_id в каждом кандидатном JSONL и выбрать тот, где больше совпадений.

### Новое воспроизведение (2026-04-09, session 891fbac2 vs 1763be29, sproektirui)

1. Чат A (session `891fbac2`) — T153 codereview (текущий)
2. Чат B (session `1763be29`) — T152 codereview (параллельный)
3. Чат C (session `e12a7106`) — T152 codereview (ещё один параллельный)
4. Чат D (session `e5f31259`) — `/intro`

Чат A выполнил `/archive-session`. `ls -t *.jsonl | head -1` выбрал `1763be29` (T152) вместо `891fbac2` (T153) — 4 JSONL файла имели mtime в диапазоне 14:56-14:57, `ls -t` выбрал произвольный. Результат: archive `1763be29` записан с T153 summary но T152 transcript/diffs.

**Обнаружение:** `/verify-archive` проверил первое user message в transcript (`t152 /codereview` ≠ `t153 /codereview`), нашёл несоответствие, перебрал candidate JSONL по `grep "t153"` и идентифицировал правильный файл.

**Фикс:** перезапущен `archive-current --jsonl <правильный>`. Первый (ошибочный) архив `1763be29` помечен SA-T071 комментарием, summary исправлен на T152.

## Связанные баги

- SA-T052 (phantom diffs from git) — рецидив при capture чужого JSONL
- SA-T060 (phantom artifacts from git status) — аналогично

### Третье воспроизведение (2026-04-10, session 425e294e vs 3990d229, autodev-v2)

1. Чат A (session `425e294e`) — `t051 /codereview` (текущий)
2. Чат B (session `3990d229`) — `t051 /smoketest` (параллельный, стартанул на 8 секунд позже)

Обе сессии работали на одной ветке `codex/pipeline-hardening-stageb-finalize` с mtime в диапазоне 19:23-19:45. Чат A выполнил `/archive-session` → `ls -t $JSONL_DIR/*.jsonl | head -1` выбрал `3990d229` (потому что в момент вызова он был newest). Script записал export `2026-04-10_autodev-v2_claude_3990d229.md` с:
- **Summary** из `--summary` аргумента чата A (codereview ADV-T051 с HIGH finding на advanceMajorCycle)
- **Transcript** из JSONL сессии B (smoketest: `t051 /smoketest`, создание `smoketest_t051_test.go`, 5 smoke сценариев, SMOKE-T051-01 finding)
- **msg_count=14** (частичный — `--tool-ids` от чата A не матчились в JSONL чата B, поэтому tool_ids fallback ловил только sessionId-matched messages)
- **tool_call_count=70** (из JSONL чата B)

Параллельно чат B тоже вызвал `/archive-session` и `/verify-archive` на тот же файл экспорта — записал 3 HTML-комментария с фиксами phantom artifacts/diffs от git working-tree contamination.

**Обнаружение (2026-04-10 verify-archive в чате A после компакта):** чат A после контекст-компакта запустил `/verify-archive`, прочитал transcript и обнаружил первое user message `t051 /smoketest` — это НЕ совпадает с тем что чат A делал (`t051 /codereview`). Проверил актуальный JSONL чата A (`425e294e`) — там первое user message действительно `t051 /codereview`. Mismatch подтверждён.

**Фикс:**
1. Summary для `3990d229` в export и SQLite восстановлен под фактическое содержимое (smoketest).
2. Чат A (`425e294e`) переархивирован с явным `--jsonl` → создан новый export `2026-04-10_autodev-v2_claude_425e294e.md`.
3. Этот раздел добавлен в SA-T071 как третье воспроизведение.

**Симптомы капчер-бага, зафиксированные в этом воспроизведении:**
- `msg_count` сильно меньше реального (14 при 86 user messages в JSONL) — первый сигнал wrong JSONL
- Summary описывает работу, которой нет в transcript'е — второй сигнал
- Первое user message в transcript начинается с command'а, которого юзер в этом чате не запускал — третий сигнал
- Archive файл для current session не создан (вместо него перезаписан чужой)

**Предложение по auto-detection в `/verify-archive`:**
Добавить проверку: сверить первое user message в transcript'е с первым user message текущего JSONL (из `find_current_jsonl` или передано skill'ом). Если не совпадает → немедленно предупредить "wrong JSONL captured (SA-T071 recurrence)" и предложить re-archive с явным `--jsonl`.

**Предложение по фиксу skill template `/archive-session`:**
Определить текущий session_id до вызова скрипта. Claude Code пишет его в env/path; если доступно — передавать `--session-id` и требовать от script'а выбирать JSONL по совпадению `sessionId` внутри самого файла (не по mtime). Это делает mtime-race невозможным.

### Четвёртое воспроизведение (2026-04-12, session 2824732a vs 088d7e4a, autodev-v2)

1. Чат A (session `2824732a`) — ADV-T046 реализация (WorktreeManager refactor, 43 messages, ~41 tool calls)
2. Чат B (session `088d7e4a`) — `/smoketest t057` → отклонение как рефакторинг (6 messages)

Чат A выполнил `/archive-session` с `--tool-ids` (41 ID). `ls -t *.jsonl | head -1` выбрал `088d7e4a` (Чат B), потому что mtime обоих JSONL были обновлены одновременно (оба чата работали в одном проекте). Результат:
- Экспорт `2026-04-12_autodev-v2_claude_088d7e4a.md` записан с T046 summary но T057-smoketest transcript/diffs
- Ранее записанный чатом B архив `088d7e4a` (smoketest T057) перезаписан T046 summary

**Обнаружение:** `/verify-archive` в этом же чате прочитал transcript → первое user message `t057 /smoketest` не совпадает с работой T046. Grep по tool_ids в candidate JSONL идентифицировал правильный файл `2824732a`.

**Дополнительные баги при cross-session capture:**
- **Artifacts/diffs** — скрипт использует `git diff HEAD` для diffs, что захватывает ВСЕ uncommitted changes на ветке (от всех предыдущих сессий), а не только изменения текущей сессии. Это рецидив SA-T075/SA-T076/SA-T084
- **Open Issues** — парсер захватил внутренний монолог ассистента ("I have enough context now...") как open issue. Рецидив SA-T080
- **Tasks** — пустой список (tool_ids не матчились → парсер не нашёл task references). Лучше, чем phantom tasks, но всё равно ошибка

**Фикс:**
1. Перезапущен `archive-current --jsonl 2824732a...` → создан корректный export `2026-04-12_autodev-v2_claude_2824732a.md`
2. Artifacts, tasks, diffs в export и SQLite исправлены вручную на фактические T046 изменения
3. Summary для `088d7e4a` в SQLite восстановлен под smoketest T057
