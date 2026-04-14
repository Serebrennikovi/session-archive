**Дата:** 2026-04-14
**Статус:** open
**Severity:** MEDIUM

# SA-T086: tool_call_count считает только переданные tool-ids, не все вызовы

## Проблема

При `archive-current --tool-ids '[...]'` скрипт записывает `tool_calls = len(tool_ids)` (4), а не реальное количество tool calls в сессии (~36). Tool IDs передаются для определения границы сессии, но используются как source of truth для подсчёта.

## Воспроизведение

Сессия `dbb7d694` — 25 сообщений, ~36 tool calls (Glob, Read, Bash, Grep, Edit, Agent, Skill). Записано: `tool_calls = 4` (ровно столько, сколько Agent tool_ids было передано).

## Ожидание

`tool_call_count` должен считаться из JSONL (количество `tool_use` блоков в сообщениях ассистента), а не из `--tool-ids`.

## Рекомендация

В `session_archive.py` → функция, формирующая metadata: считать tool calls из parsed JSONL (count of `tool_use` content blocks), а `--tool-ids` использовать только для session boundary filtering.
