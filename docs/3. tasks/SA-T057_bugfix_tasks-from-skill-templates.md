**Дата:** 2026-04-08
**Статус:** draft
**Источник:** verify-archive сессии 6210a39a

# SA-T057 — Фантомные задачи из шаблонов скиллов

## Баг

Парсер извлекает task IDs из **шаблонов и примеров** внутри скиллов (/codereview, /smoketest), а не из реальной работы сессии.

**Воспроизведение:** сессия 6210a39a работала только с ADV-T032. Парсер нашёл 7 задач:
- `T001` — из примера в шаблоне smoketest (`"task T001 started"`)
- `T042` — из шаблона codereview (`T042`, `t042`)
- `T099` — из примера в тексте code review findings
- `T024`, `T048` — упомянуты в контексте HANDOFF/спеки, не работали с ними

**Причина:** task extraction не фильтрует task IDs из:
1. `<command-message>` / skill template content (XML-блоки с описанием скиллов)
2. Markdown-примеров и шаблонов (`| 1 | happy | ... | exit 0, "task T001 started" |`)
3. Контекстных упоминаний в прочитанных файлах (HANDOFF содержит все задачи проекта)

**Impact:** session_tasks содержит 6 phantom tasks, делая поиск по задачам unreliable.

## Рекомендация

1. Игнорировать task IDs внутри `<command-message>` блоков
2. Игнорировать task IDs внутри markdown code blocks (` ``` `) и inline code (`` ` ``)
3. Различать "mentioned in read file" vs "actively worked on" — task ID из Read tool_result не означает работу с задачей
4. Проверять: был ли хотя бы один Edit/Write/Bash для файла, содержащего этот task ID?

## Прецедент #2 — session 1dbec8ba (sproektirui, 2026-04-09)

Сессия `/visualcheck T148` работала только с T148. Парсер записал 3 задачи:
- `T042` — из шаблона `/visualcheck` (примеры: `T{042}`, `t042`)
- `T099` — из шаблона `/archive-session` (пример: `T099`)
- `T148` — реальная задача (корректно)

Паттерн идентичен прецеденту #1: шаблоны скиллов содержат placeholder task IDs (`T042`, `T099`) которые парсер не фильтрует.

## Прецедент #3 — session d3dae777 (sproektirui, 2026-04-09)

Сессия `/visualcheck + /smoketest T149` работала только с T149. Парсер записал 7 задач:
- `T001` — из шаблона `/smoketest` (пример: `"task T001 started"`)
- `T024`, `T048` — из шаблона `/smoketest` (примеры scenario descriptions)
- `T032` — из шаблона `/smoketest` (пример UPSERT сценария)
- `T042` — из шаблона `/visualcheck` (примеры `T{042}`, `t042`)
- `T099` — из шаблона `/visualcheck` (пример: `T099, JIRA-123`)
- `T149` — реальная задача (корректно)

Паттерн устойчив: при каждом вызове `/visualcheck` + `/smoketest` добавляется 6 phantom tasks.

## Прецедент #4 — session f8a14e62 (sproektirui, 2026-04-09)

Сессия: `/visualcheck T151`. Реально работали ТОЛЬКО с T151. Парсер записал Tasks: `T042, T099, T151`.

- `T042` — из шаблона `/visualcheck` (пример: `T{042}`, `t042`, `042`)
- `T099` — из шаблона `/visualcheck` (пример: `T099, JIRA-123`)
- `T151` — реальная задача (корректно)

Паттерн полностью идентичен прецедентам #1–#3. Ложные задачи удалены вручную из SQLite и export .md.
