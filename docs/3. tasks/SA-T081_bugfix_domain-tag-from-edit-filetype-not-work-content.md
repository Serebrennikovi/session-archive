**Дата:** 2026-04-12
**Статус:** open
**Sev:** MEDIUM

# SA-T081 — Domain-тег определяется по типу Edit-файла, а не по содержанию работы

## Проблема

Сессия, целиком посвящённая код-ревью Go integration tests, получает `domain: docs` потому что единственный Edit-вызов был на `.md` файл (task file с findings). При этом 12 Read-вызовов были на `.go` файлы, и вся содержательная работа — анализ Go-кода.

## Воспроизведение

Сессия `31408eb9` (autodev-v2, 2026-04-12):
- 12 Read на `.go` файлы (integration tests, mock executor, engine)
- 1 Edit на `.md` файл (записать findings в task file)
- Domain-тег: `docs` (wrong), ожидается: `testing`, `go`

## Root cause

`detect_domains()` (предположительно) считает Edit/Write артефакты приоритетнее Read, и определяет домен по расширению файла. Для `.md` → `docs`. Но в code review сессии основная работа — чтение кода, а Edit .md — побочный артефакт записи результатов.

## Рекомендация

При определении domain учитывать:
1. **Соотношение типов файлов** по всем артефактам (read + modified), не только по modified
2. **Skill-контекст**: если skill = `codereview*` → domain должен определяться по типу файлов в Read, а не в Edit
3. Fallback: если >70% Read-артефактов одного типа (`.go`, `.py`, `.ts`) — domain = этот тип, даже если Edit был на другой

Связан с SA-T008 (domain context drift), но это другой класс: не фантомные теги из текста, а неправильный приоритет file types.

### Воспроизведение 2 (2026-04-13, session `ba9d7314`)

Сессия: `/codereview t026` на autodev-v2. 10 Read на `.go` файлы (scheduler, worker, dag, runner, interfaces, tests), 1 Read на `.md` spec, 1 Edit на `.md` task file. Domain-тег: `docs` (wrong), ожидается: `go`. Идентичный паттерн с воспроизведением 1.
