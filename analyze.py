#!/usr/bin/env python3
"""
Session Archive — аналитика поверх sessions.db

Usage:
  python3 analyze.py                    # все отчёты
  python3 analyze.py <report_name>      # один отчёт

Reports:
  summary        Общая статистика по всем сессиям
  projects       Активность по проектам
  tasks          Топ задач (сколько сессий на задачу)
  events         Частота событий (deploy, tests, commit...)
  domains        Какие домены трогали чаще всего
  timeline       Активность по дням
  artifacts      Самые изменяемые файлы
  models         Использование AI моделей
  deep <project> Детальный отчёт по проекту
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import Counter

DB_PATH = Path(__file__).parent / "data" / "sessions.db"

def get_db():
    if not DB_PATH.exists():
        print(f"БД не найдена: {DB_PATH}")
        print("Сначала заархивируй хотя бы одну сессию: /archive-session")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def q(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()

def hr(title=""):
    print(f"\n{'─' * 60}")
    if title:
        print(f"  {title}")
        print(f"{'─' * 60}")

# ── Reports ───────────────────────────────────────────────────────────────────

def report_summary(conn):
    hr("ОБЩАЯ СТАТИСТИКА")
    row = q(conn, """
        SELECT
          COUNT(*)                           AS total_sessions,
          COUNT(DISTINCT repo_name)          AS projects,
          SUM(msg_count)                     AS total_messages,
          SUM(tool_call_count)               AS total_tool_calls,
          AVG(msg_count)                     AS avg_msgs,
          AVG(tool_call_count)               AS avg_tools,
          MIN(created_at)                    AS first_session,
          MAX(created_at)                    AS last_session
        FROM sessions
    """)[0]

    print(f"  Сессий всего:      {row['total_sessions']}")
    print(f"  Проектов:          {row['projects']}")
    print(f"  Сообщений всего:   {row['total_messages']}")
    print(f"  Tool calls всего:  {row['total_tool_calls']}")
    print(f"  Среднее msgs:      {row['avg_msgs']:.1f}" if row['avg_msgs'] else "")
    print(f"  Среднее tools:     {row['avg_tools']:.1f}" if row['avg_tools'] else "")
    print(f"  Первая сессия:     {(row['first_session'] or '')[:10]}")
    print(f"  Последняя:         {(row['last_session'] or '')[:10]}")

    # tasks
    task_count = q(conn, "SELECT COUNT(DISTINCT task_id) FROM session_tasks")[0][0]
    print(f"  Задач упомянуто:   {task_count}")

def report_projects(conn):
    hr("АКТИВНОСТЬ ПО ПРОЕКТАМ")
    rows = q(conn, """
        SELECT
          repo_name,
          COUNT(*)              AS sessions,
          SUM(msg_count)        AS messages,
          SUM(tool_call_count)  AS tool_calls,
          MAX(created_at)       AS last_active
        FROM sessions
        GROUP BY repo_name
        ORDER BY sessions DESC
    """)
    print(f"  {'Проект':25s}  {'Сессий':>7}  {'Msgs':>6}  {'Tools':>6}  Последняя")
    print(f"  {'─'*25}  {'─'*7}  {'─'*6}  {'─'*6}  {'─'*10}")
    for r in rows:
        name = (r['repo_name'] or 'unknown')[:25]
        print(f"  {name:25s}  {r['sessions']:>7}  {r['messages']:>6}  {r['tool_calls']:>6}  {(r['last_active'] or '')[:10]}")

def report_tasks(conn):
    hr("ТОП ЗАДАЧ")
    rows = q(conn, """
        SELECT
          st.task_id,
          COUNT(DISTINCT st.session_id)  AS sessions,
          GROUP_CONCAT(DISTINCT s.repo_name) AS projects,
          GROUP_CONCAT(DISTINCT st.actions)  AS actions
        FROM session_tasks st
        JOIN sessions s ON s.id = st.session_id
        GROUP BY st.task_id
        ORDER BY sessions DESC
        LIMIT 30
    """)
    if not rows:
        print("  Нет данных о задачах")
        return
    print(f"  {'Задача':10s}  {'Сессий':>7}  {'Проекты':30s}  Действия")
    print(f"  {'─'*10}  {'─'*7}  {'─'*30}  {'─'*20}")
    for r in rows:
        projects = (r['projects'] or '')[:30]
        actions  = (r['actions']  or '')[:20]
        print(f"  {r['task_id']:10s}  {r['sessions']:>7}  {projects:30s}  {actions}")

def report_events(conn):
    hr("ЧАСТОТА СОБЫТИЙ")
    rows = q(conn, """
        SELECT event_type, COUNT(*) AS cnt
        FROM session_events
        GROUP BY event_type
        ORDER BY cnt DESC
    """)
    if not rows:
        print("  Нет данных о событиях")
        return
    max_cnt = max(r['cnt'] for r in rows)
    for r in rows:
        bar = '█' * int(r['cnt'] / max_cnt * 30)
        print(f"  {r['event_type']:20s}  {r['cnt']:4d}  {bar}")

def report_domains(conn):
    hr("ДОМЕНЫ (что чаще трогали)")
    rows = q(conn, """
        SELECT value, COUNT(*) AS cnt
        FROM session_tags
        WHERE category = 'domain'
        GROUP BY value
        ORDER BY cnt DESC
    """)
    if not rows:
        print("  Нет тегов по доменам")
        return
    max_cnt = max(r['cnt'] for r in rows)
    for r in rows:
        bar = '█' * int(r['cnt'] / max_cnt * 30)
        print(f"  {r['value']:20s}  {r['cnt']:4d}  {bar}")

def report_timeline(conn):
    hr("АКТИВНОСТЬ ПО ДНЯМ")
    rows = q(conn, """
        SELECT
          SUBSTR(created_at, 1, 10)  AS day,
          COUNT(*)                   AS sessions,
          SUM(msg_count)             AS messages
        FROM sessions
        GROUP BY day
        ORDER BY day DESC
        LIMIT 30
    """)
    if not rows:
        print("  Нет данных")
        return
    max_s = max(r['sessions'] for r in rows)
    print(f"  {'День':12s}  {'Сессий':>7}  {'Msgs':>6}  ")
    for r in rows:
        bar = '█' * int(r['sessions'] / max_s * 20)
        print(f"  {r['day']:12s}  {r['sessions']:>7}  {r['messages']:>6}  {bar}")

def report_artifacts(conn):
    hr("САМЫЕ ИЗМЕНЯЕМЫЕ ФАЙЛЫ (created/modified)")
    rows = q(conn, """
        SELECT
          file_path,
          COUNT(*)             AS touched,
          COUNT(DISTINCT session_id) AS sessions,
          GROUP_CONCAT(DISTINCT action) AS actions
        FROM session_artifacts
        WHERE action IN ('created', 'modified')
          AND file_path NOT LIKE 'event:%'
        GROUP BY file_path
        ORDER BY touched DESC
        LIMIT 25
    """)
    if not rows:
        print("  Нет данных об артефактах")
        return
    print(f"  {'Файл':50s}  {'Раз':>5}  {'Сессий':>7}  Действия")
    print(f"  {'─'*50}  {'─'*5}  {'─'*7}  {'─'*15}")
    for r in rows:
        fp = r['file_path'][-50:]
        print(f"  {fp:50s}  {r['touched']:>5}  {r['sessions']:>7}  {r['actions']}")

def report_models(conn):
    hr("МОДЕЛИ AI")
    rows = q(conn, """
        SELECT ai_model, COUNT(*) AS sessions, SUM(msg_count) AS messages
        FROM sessions
        GROUP BY ai_model
        ORDER BY sessions DESC
    """)
    for r in rows:
        print(f"  {r['ai_model']:30s}  {r['sessions']:4d} сессий  {r['messages']:6d} msgs")

def report_deep(conn, project):
    rows = q(conn, """
        SELECT id, created_at, branch, msg_count, tool_call_count, summary
        FROM sessions
        WHERE repo_name LIKE ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (f"%{project}%",))

    if not rows:
        print(f"  Проект '{project}' не найден")
        return

    hr(f"ДЕТАЛЬНЫЙ ОТЧЁТ: {project}")
    for r in rows:
        print(f"\n  [{(r['created_at'] or '')[:16]}]  {r['id'][:8]}  br={r['branch'] or '?'}")
        print(f"    msgs={r['msg_count']}  tools={r['tool_call_count']}")
        if r['summary']:
            # первые 200 символов
            print(f"    {r['summary'][:200]}")

        sid = r['id']
        tasks = q(conn, "SELECT task_id, actions FROM session_tasks WHERE session_id=?", (sid,))
        if tasks:
            print(f"    tasks: {', '.join(t['task_id'] for t in tasks)}")
        events = q(conn, "SELECT event_type FROM session_events WHERE session_id=?", (sid,))
        if events:
            print(f"    events: {', '.join(e['event_type'] for e in events)}")

# ── SQL query helper ──────────────────────────────────────────────────────────

def run_query(sql):
    conn = get_db()
    try:
        rows = conn.execute(sql).fetchall()
        if not rows:
            print("(пусто)")
            return
        keys = rows[0].keys()
        widths = [max(len(k), max(len(str(r[k] or '')) for r in rows)) for k in keys]
        header = "  " + "  ".join(k.ljust(w) for k, w in zip(keys, widths))
        print(header)
        print("  " + "  ".join("─" * w for w in widths))
        for row in rows:
            print("  " + "  ".join(str(row[k] or '').ljust(w) for k, w in zip(keys, widths)))
    except sqlite3.OperationalError as e:
        print(f"SQL error: {e}")
    finally:
        conn.close()

# ── Main ──────────────────────────────────────────────────────────────────────

ALL_REPORTS = [
    ("summary",   report_summary),
    ("projects",  report_projects),
    ("tasks",     report_tasks),
    ("events",    report_events),
    ("domains",   report_domains),
    ("timeline",  report_timeline),
    ("artifacts", report_artifacts),
    ("models",    report_models),
]

if __name__ == "__main__":
    conn = get_db()
    args = sys.argv[1:]

    if not args:
        for name, fn in ALL_REPORTS:
            fn(conn)
        print()
    elif args[0] == "deep" and len(args) >= 2:
        report_deep(conn, args[1])
    elif args[0] == "query" and len(args) >= 2:
        conn.close()
        run_query(" ".join(args[1:]))
        sys.exit(0)
    else:
        name = args[0]
        fn_map = dict(ALL_REPORTS)
        if name in fn_map:
            fn_map[name](conn)
        else:
            print(f"Неизвестный отчёт: {name}")
            print(f"Доступные: {', '.join(fn_map.keys())}, deep <project>, query <sql>")

    conn.close()
    print()
