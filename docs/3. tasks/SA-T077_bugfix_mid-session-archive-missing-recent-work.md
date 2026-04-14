# SA-T077 — Mid-session archive misses recent work (transcript + summary + artifacts)

**Дата:** 2026-04-12
**Severity:** HIGH
**Обнаружено:** verify-archive сессия `fa809fcb` (AutoDev v2, 2026-04-11)

## Описание

Когда `/archive-session` вызывается в середине активной Claude Code сессии (т.е. после нескольких conversation turns, но до завершения сессии), архив захватывает **только часть работы**:

1. **Transcript неполный** — JSONL ещё не содержит сообщений текущего conversation turn (Claude Code flush'ит JSONL асинхронно). Работа, сделанная в последнем блоке (между предпоследним и текущим сообщением пользователя), отсутствует в транскрипте.

2. **Summary расхождение** — Claude формулирует summary из conversation context (полный), но скрипт экстрагирует metadata из JSONL (неполный). Результат: summary описывает T034 fix, а transcript его не содержит.

3. **Artifacts неполные** — скрипт извлекает artifacts из JSONL tool calls. Файлы, прочитанные/изменённые в текущем conversation turn, не попадают в artifacts list.

4. **Diffs корректны** — git diff захватывает ВСЕ uncommitted изменения, включая текущие. Поэтому Diffs показывают T034 правки, а Artifacts — нет.

## Воспроизведение

1. Начать сессию с `/intro` + `/fix T045`
2. В том же conversation turn сделать `/fix T034`
3. Вызвать `/archive-session`
4. Результат: transcript содержит только T045 работу; T034 — только в summary и diffs

## Ожидаемое поведение

Архив должен содержать ВСЕ работу текущей сессии, включая незавершённый conversation turn.

## Возможные решения

1. **Re-archive при завершении сессии** — Claude Code hook `on_session_end` перезаписывает запись. Требует hooks support (из settings.json).

2. **Two-pass extraction** — первый pass из JSONL (то что есть), второй pass из conversation context (Claude перечисляет tool calls текущего turn). Команда `/archive-session` уже собирает `--tool-ids`, но скрипт их не использует для дополнения transcript.

3. **Delay flush** — попросить пользователя вызывать `/archive-session` в **новом** conversation turn после завершения работы (т.е. как отдельное сообщение). Это workaround, не fix.

4. **Post-archive update** — повторный вызов `/archive-session` после завершения сессии автоматически перезаписывает запись с полными данными (уже поддерживается — `session_id` is upsert key).

## Связь с другими багами

- **SA-T073** (cross-session contamination) — обратная сторона проблемы: T073 про лишние данные из прошлых сессий в одном JSONL, T077 про недостающие данные текущей сессии.
- **SA-T075** (diffs from uncommitted prior sessions) — дополняет: diffs захватывают всё (включая prior), а artifacts/transcript — не всё (из-за JSONL timing).
