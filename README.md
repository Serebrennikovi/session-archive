# Session Archive

Система сохранения и анализа диалогов с AI-ассистентами (Claude Code, OpenAI Codex и др.).

## Куда складываются данные

```
12_SessionArchive/
  data/
    sessions.db          ← SQLite-база со всеми сессиями
    exports/
      2026-03-25_AutoDev_ff5cd8a8.md   ← markdown-транскрипт каждой сессии
      2026-03-25_CallsBot_a1b2c3d4.md
      ...
```

**Что хранится в БД:**

| Таблица | Что содержит |
|---------|-------------|
| `sessions` | Каждая сессия: проект, репо, ветка, модель, summary, кол-во сообщений |
| `session_tags` | Теги: проект, домен (frontend/backend/...), модель |
| `session_tasks` | T### задачи, упомянутые в сессии |
| `session_artifacts` | Файлы, которые создавались/редактировались/читались |
| `session_events` | События: deploy, tests_run, commit_made, pr_created, handoff_read... |

## Использование

### 1. Сохранить сессию (в конце каждого чата)

В Claude Code чате:
```
/archive-session
```

Это команда-навык. Claude автоматически найдёт JSONL файл текущей сессии,
распарсит, напишет summary, проставит теги и сохранит в БД.

### 2. Посмотреть статистику

```bash
# Общий дашборд (все отчёты)
python3 analyze.py

# Один отчёт
python3 analyze.py summary
python3 analyze.py projects
python3 analyze.py tasks
python3 analyze.py timeline
python3 analyze.py events
python3 analyze.py artifacts

# Детально по проекту
python3 analyze.py deep CallsBot
python3 analyze.py deep AutoDev

# Произвольный SQL
python3 analyze.py query "SELECT repo_name, COUNT(*) FROM sessions GROUP BY repo_name"
```

### 3. Веб-дашборд через Datasette

Datasette — zero-code веб-интерфейс для SQLite. Фильтры, сортировка, SQL, графики.

```bash
pip install datasette
datasette data/sessions.db
# открывается http://localhost:8001
```

Готовые запросы для Datasette (сохрани в `datasette_queries.json` рядом с `sessions.db`):

```json
{
  "sessions.db": {
    "queries": {
      "Сессии по дням": "SELECT SUBSTR(created_at,1,10) as day, COUNT(*) as sessions, SUM(msg_count) as messages FROM sessions GROUP BY day ORDER BY day DESC",
      "Топ задач": "SELECT task_id, COUNT(*) as sessions FROM session_tasks GROUP BY task_id ORDER BY sessions DESC LIMIT 20",
      "События": "SELECT event_type, COUNT(*) as cnt FROM session_events GROUP BY event_type ORDER BY cnt DESC",
      "Самые изменяемые файлы": "SELECT file_path, COUNT(*) as touched FROM session_artifacts WHERE action IN ('created','modified') AND file_path NOT LIKE 'event:%' GROUP BY file_path ORDER BY touched DESC LIMIT 20",
      "Последние сессии": "SELECT id, SUBSTR(created_at,1,16) as date, repo_name, branch, msg_count, tool_call_count, summary FROM sessions ORDER BY created_at DESC LIMIT 50"
    }
  }
}
```

```bash
datasette data/sessions.db --metadata datasette_queries.json
```

### 4. Быстрая статистика из терминала

```bash
python3 session_archive.py stats
```

## Совместимость

| Среда | Поддержка |
|-------|-----------|
| Claude Code (CLI) | ✅ Полная — JSONL парсится автоматически |
| OpenAI Codex | ⚠️ Частичная — транскрипт пустой, метаданные вручную |
| Любой AI чат | ⚠️ Частичная — запускай `/archive-session` вручную |

## Схема БД

```sql
sessions (id, created_at, ended_at, project_path, repo_name, branch,
          ai_model, summary, msg_count, user_msg_count, tool_call_count,
          export_path, raw_jsonl_path)

session_tags      (session_id, category, value)
session_tasks     (session_id, task_id, actions)
session_artifacts (session_id, file_path, action, is_code, is_doc)
session_events    (session_id, event_type, detail)
```

## Файлы

| Файл | Назначение |
|------|------------|
| `session_archive.py` | CLI: parse/write/stats/query |
| `analyze.py` | Аналитические отчёты |
| `data/sessions.db` | БД (не в git) |
| `data/exports/` | Markdown-транскрипты (не в git) |
| `~/.claude/commands/archive-session.md` | Глобальный навык `/archive-session` |
