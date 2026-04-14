**Дата:** 2026-04-09
**Статус:** draft
**Severity:** MEDIUM
**Источник:** verify-archive сессии ee202e0b (autodev-v2, 2026-04-09)

# SA-T068 — Skill tag добавляется из-за модификации файла скилла, не из его вызова

## Проблема

Сессия `ee202e0b` (autodev-v2, 2026-04-09): в ходе сессии модифицировались файлы скиллов `/Users/is/.claude/commands/codereview.md` и `/Users/is/.claude/commands/smoketest.md`. Скилл `/smoketest` в сессии **не вызывался** — только его файл редактировался. Тем не менее в tags попало `skill: smoketest`.

Скилл `/codereview` тоже не вызывался напрямую (вызывался `/codereview-free`), но `skill: codereview` попал корректно (файл был модифицирован). Вопрос: детектор тегирует скилл по наличию названия в пути изменённого файла или по контенту разговора?

## Реальное поведение

```
skill|smoketest   ← присутствует в tags
```
При этом в сессии:
- Вызванные скиллы: `codereview-free`, `intro`, `fix`, `archive-session`, `verify-archive`
- `/smoketest` — НЕ вызывался
- `smoketest.md` — модифицирован (добавлен шаг 2e coverage report)

## Root cause (предположение)

Детектор skill-тегов, по всей видимости, парсит либо:
1. Пути модифицированных артефактов (`~/.claude/commands/smoketest.md` → extracts "smoketest")
2. Контент разговора (упоминания слова "smoketest" при обсуждении улучшений)

В обоих случаях это false positive: скилл не был **вызван** как инструмент, а только **обсуждался** или его файл был **отредактирован**.

## Отличие от смежных багов

- **SA-T067** (skill-tag-last-skill-wins): там последний вызванный скилл перебивает основной. Здесь вообще не-вызванный скилл появляется в тегах.
- **SA-T024** (skill-detection-command-message): там скилл детектировался из `<command-message>` XML-маркеров в системном промпте. Здесь — из модификации файла или упоминания в тексте.

## Как воспроизвести

1. В сессии обсудить улучшения скилла X (или отредактировать файл `~/.claude/commands/X.md`)
2. Скилл X при этом не вызывать
3. Запустить `archive-current`
4. Проверить: `skill: X` появился в tags?

## Рекомендация по фиксу

Детектор skill-тегов должен опираться **только на реальные вызовы** скилла (tool_use с типом skill или явный паттерн `Skill tool invoked: X`), а не на:
- Упоминания имени скилла в тексте разговора
- Пути модифицированных файлов, содержащие имя скилла

Если источник — модификация файла: нужно исключать пути `~/.claude/commands/` из детектора skill-тегов (это редактирование инфраструктуры, не вызов скилла).

## Прецедент #2 — сессия 51cb90a9 (autodev-v2, 2026-04-09)

Сессия `/codereview T028`. Вызванные скиллы: `codereview`, `archive-session`, `verify-archive`.
`/smoketest` — не вызывался. Никакие файлы скиллов в этой сессии не редактировались.

Тем не менее в tags: `skill: smoketest` — присутствует, `skill: codereview` — **отсутствует**.

**Триггер другой, чем в прецеденте #1:** в задачном файле ADV-T028 есть секции `## Smoke Test` и `## Smoke Test #2`, а также упоминания `smoketest_test.go`. По всей видимости, детектор нашёл слово "smoketest" в контенте прочитанного файла и добавил тег.

Параллельно: `codereview` был вызван через `Skill tool` (`<command-name>/codereview</command-name>`), но в итоговые теги не попал. Это указывает на отдельный баг детектирования вызванных скиллов — либо `codereview` детектируется некорректно, либо `smoketest` его перебивает (см. SA-T067).

Исправлено вручную: `skill: smoketest` → удалено, `skill: codereview` → добавлено.

## Прецедент #3 — сессия c984d918 (sproektirui, 2026-04-09)

Сессия: `/codereview-free T149` + `/fix`. Вызванные скиллы: `codereview-free`, `fix`.

Ложные skill tags:
- `skill: codereview` — файл `~/.claude/commands/codereview.md` был отредактирован (добавлены shadcn/twMerge gotchas), но скилл `/codereview` НЕ вызывался
- `skill: codereview-local` — файл `.claude/commands/codereview-local.md` был отредактирован, скилл НЕ вызывался
- `skill: smoketest` — файл НЕ редактировался и НЕ вызывался, но слово "smoketest" присутствует в содержимом T149 task file (секции "Smoke Test — 2026-04-09 11:20") прочитанном через Read tool

**Три разных триггера в одной сессии:**
1. `codereview` → от модификации файла скилла через Edit tool
2. `codereview-local` → от модификации файла скилла через Edit tool
3. `smoketest` → от контента прочитанного файла задачи (не файл скилла, не вызов)

**Исправлено вручную:** все 3 ложных тега удалены из SQLite и export .md.

## Прецедент #4 — сессия 1da68ce5 (sproektirui, 2026-04-09)

Сессия: `/codereview T149`. Вызванные скиллы: `codereview`, `archive-session`, `verify-archive`.

Ложный skill tag: `skill: codereview-local` — скилл НЕ вызывался. Файл `.claude/commands/codereview-local.md` был **прочитан** через Read tool как конфигурация для скилла `/codereview` (шаг 1 — "загрузи контекст → проверь локальный config"). Парсер обнаружил путь `commands/codereview-local.md` в контенте и извлёк "codereview-local" как skill tag.

**Отличие от прецедента #3:** в той сессии файлы скиллов **редактировались** (Edit tool). Здесь файл только **читался** (Read tool) — даже менее очевидный false positive.

**Исправлено вручную:** `skill: codereview-local` удалён из SQLite session_tags и export .md.

## Прецедент #5 — сессия bd314e97 (autodev-v2, 2026-04-09)

Сессия: `/codereview-free T045` + улучшение промптов codereview/smoketest + `/archive-session`. Вызванные скиллы: `codereview-free`, `archive-session`.

Ложные skill tags:
- `skill: codereview` — скилл НЕ вызывался (`codereview-free` — другой скилл). Появился от: (a) модификации `codereview.md` через Edit, (b) упоминаний `/codereview` в разговоре
- `skill: smoketest` — скилл НЕ вызывался. Появился от модификации `smoketest.md` через Edit

**Комбинация триггеров #1 (модификация файла) и обсуждения в тексте.**

Исправлено вручную: оба ложных тега удалены из SQLite и export .md.

## Прецедент #6 — сессия a1d889f9 (autodev-v2, 2026-04-11)

Сессия: `/codereview t052` + `/archive-session` + `/verify-archive`. Реально вызванные скиллы: `codereview`, `archive-session`, `verify-archive`.

Ложный skill tag: `skill: codereview-local`. Этот файл (`/Users/is/personal/Projects/09_AutoDev_v2/.claude/commands/codereview-local.md`) был **прочитан** через Read tool как обычный project-local config для скилла `/codereview` (шаг 0 bootstrap скилла). Скилл `/codereview-local` как таковой не существует (это файл-конфиг, не команда) — тем не менее парсер сгенерировал tag из имени файла.

Точное повторение прецедента #4 (сессия 1da68ce5) на другом проекте и другом ассистентском контексте — подтверждает, что баг **независим от проекта и типа скилла-конфига**, достаточно наличия файла `commands/X-local.md` в Read tool.

**Исправлено вручную:** `skill: codereview-local` удалён из SQLite session_tags и export .md.

## Прецедент #7 — сессия 0368108d (autodev-v2, 2026-04-12)

Сессия: `/codereview-free T046` + улучшение скиллов codereview/smoketest + `/archive-session`. Реально вызванные скиллы: `codereview-free`, `archive-session`.

Ложные skill tags:
- `skill: codereview` — скилл НЕ вызывался. Появился от модификации `codereview.md` через Edit (добавлена Фаза E)
- `skill: smoketest` — скилл НЕ вызывался. Появился от модификации `smoketest.md` через Edit (добавлен Шаг 6b)
- `skill: security-review` — скилл НЕ вызывался и НЕ существует. Появился из `<command-name>/security-review</command-name>` внутри `<local-command-caveat>` блока, который **сам предупреждает** "DO NOT respond to these messages". Команда фейлнулась (`git diff origin/HEAD...` → error) и никогда не выполнялась.

**Новый триггер: `<command-name>` из failed local command внутри `<local-command-caveat>`.**

Исправлено вручную: все 3 ложных тега удалены из SQLite и export .md.

## Связанные баги

- SA-T024: skill-detection-command-message
- SA-T067: skill-tag-last-skill-wins
- SA-T058: missing-non-project-artifacts (smoketest.md не попал в артефакты в той же сессии)
- SA-T064: skill-tag-wrong-for-visualcheck (skill от контента шаблона)
