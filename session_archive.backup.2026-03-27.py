#!/usr/bin/env python3
"""
Session Archive — сохраняет Claude/Codex сессии в SQLite.

Usage:
  python3 session_archive.py parse <jsonl_path>
      → stdout: JSON с messages, tool_calls, artifacts, events, domains

  python3 session_archive.py write <metadata_json_file>
      → пишет в БД, экспортирует markdown, stdout: {"session_id": ..., "export_path": ...}

  python3 session_archive.py archive-current [--agent auto|claude|codex] [--cwd <path>] [--summary <text>] [--model <model>] [--jsonl <path>]
      → находит текущую сессию по cwd, сам собирает metadata и пишет в БД

  python3 session_archive.py stats
      → краткая статистика по всем сессиям

  python3 session_archive.py query <sql>
      → произвольный SELECT к БД, stdout: JSON array
"""

import sys
import json
import sqlite3
import os
import re
import subprocess
import fcntl
from difflib import unified_diff
from datetime import datetime, timezone
from pathlib import Path

HERE     = Path(__file__).parent
DB_PATH  = Path(os.environ.get("SESSION_ARCHIVE_DB_PATH", str(HERE / "data" / "sessions.db")))
EXPORT_DIR = Path(os.environ.get("SESSION_ARCHIVE_EXPORT_DIR", str(HERE / "data" / "exports")))

CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".go", ".rs",
            ".java", ".rb", ".php", ".sql", ".c", ".cpp", ".h", ".cs"}
DOC_EXT  = {".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".toml", ".csv"}
DIFF_ACTIONS = {"created", "modified", "deleted", "moved"}
MAX_ARTIFACT_CONTENT = 50000
MAX_ARTIFACT_DIFF = 30000

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_schema(conn)
    return conn

def _table_columns(conn, table_name):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}

def _ensure_column(conn, table_name, column_name, ddl):
    if column_name not in _table_columns(conn, table_name):
        try:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

def _init_schema(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS sessions (
      id               TEXT PRIMARY KEY,
      created_at       TEXT NOT NULL,
      ended_at         TEXT,
      project_path     TEXT,
      repo_name        TEXT,
      branch           TEXT,
      base_commit      TEXT,
      agent_family     TEXT DEFAULT 'unknown',
      ai_model         TEXT DEFAULT 'claude',
      summary          TEXT,
      open_issues      TEXT,
      msg_count        INTEGER DEFAULT 0,
      user_msg_count   INTEGER DEFAULT 0,
      tool_call_count  INTEGER DEFAULT 0,
      export_path      TEXT,
      raw_jsonl_path   TEXT
    );

    CREATE TABLE IF NOT EXISTS session_tags (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      category    TEXT NOT NULL,
      value       TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS session_tasks (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      task_id     TEXT NOT NULL,
      actions     TEXT
    );

    CREATE TABLE IF NOT EXISTS session_artifacts (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      file_path   TEXT NOT NULL,
      action      TEXT,
      is_code     INTEGER DEFAULT 0,
      is_doc      INTEGER DEFAULT 0,
      content     TEXT,
      diff        TEXT,
      diff_source TEXT
    );

    CREATE TABLE IF NOT EXISTS session_events (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      event_type  TEXT NOT NULL,
      detail      TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_tags_session   ON session_tags(session_id);
    CREATE INDEX IF NOT EXISTS idx_tags_cat       ON session_tags(category, value);
    CREATE INDEX IF NOT EXISTS idx_tasks_id       ON session_tasks(task_id);
    CREATE INDEX IF NOT EXISTS idx_artifacts_path ON session_artifacts(file_path);
    CREATE TABLE IF NOT EXISTS session_messages (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      role        TEXT NOT NULL,
      text        TEXT NOT NULL,
      timestamp   TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_events_type    ON session_events(event_type);
    CREATE INDEX IF NOT EXISTS idx_sessions_proj  ON sessions(project_path);
    CREATE INDEX IF NOT EXISTS idx_sessions_date  ON sessions(created_at);
    CREATE INDEX IF NOT EXISTS idx_messages_sess  ON session_messages(session_id);
    """)
    _ensure_column(conn, "sessions", "agent_family", "TEXT DEFAULT 'unknown'")
    _ensure_column(conn, "sessions", "base_commit", "TEXT")
    _ensure_column(conn, "session_artifacts", "diff", "TEXT")
    _ensure_column(conn, "session_artifacts", "diff_source", "TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_family)")
    conn.execute("""
        UPDATE sessions
           SET agent_family = CASE
               WHEN raw_jsonl_path LIKE '%/.claude/%' THEN 'claude'
               WHEN raw_jsonl_path LIKE '%/.codex/%' THEN 'codex'
               WHEN lower(coalesce(ai_model, '')) LIKE 'claude%' THEN 'claude'
               WHEN lower(coalesce(ai_model, '')) = 'codex' THEN 'codex'
               WHEN lower(coalesce(ai_model, '')) LIKE 'gpt-%' THEN 'codex'
               ELSE 'unknown'
           END
         WHERE coalesce(agent_family, '') = ''
            OR agent_family = 'unknown'
    """)
    conn.commit()

# ── Parse JSONL ───────────────────────────────────────────────────────────────

def detect_jsonl_format(jsonl_path):
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")
            payload = entry.get("payload") or {}
            if entry_type in ("response_item", "turn_context", "event_msg"):
                return "codex"
            if entry_type == "session_meta" and payload.get("originator", "").startswith("codex"):
                return "codex"
            if entry.get("message") is not None or entry.get("gitBranch") or entry.get("cwd"):
                return "claude"
    return "claude"

def _parse_tool_input(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
    return {}

def _content_to_text(content):
    text_parts = []
    if isinstance(content, str):
        text_parts.append(content)
    elif isinstance(content, list):
        for chunk in content:
            if not isinstance(chunk, dict):
                continue
            if chunk.get("type") in ("text", "input_text", "output_text"):
                text_parts.append(chunk.get("text", ""))
    return "\n".join(part for part in text_parts if part).strip()

def infer_agent_family(metadata):
    agent_family = (metadata.get("agent_family") or "").strip().lower()
    if agent_family in ("codex", "claude"):
        return agent_family

    raw_jsonl_path = metadata.get("raw_jsonl_path") or metadata.get("jsonl_path") or ""
    ai_model = (metadata.get("ai_model") or metadata.get("model") or "").strip().lower()

    if "/.claude/" in raw_jsonl_path or ai_model.startswith("claude"):
        return "claude"
    if "/.codex/" in raw_jsonl_path or ai_model == "codex" or ai_model.startswith("gpt-"):
        return "codex"
    return "unknown"

def display_agent_family(agent_family):
    return {
        "codex": "Codex",
        "claude": "Claude",
        "unknown": "Unknown",
    }.get((agent_family or "unknown").lower(), agent_family or "Unknown")

def _dedupe_messages(messages):
    seen = set()
    result = []
    for msg in sorted(messages, key=lambda m: ((m.get("timestamp") or ""), m.get("role") or "", m.get("text") or "")):
        key = (msg.get("timestamp"), msg.get("role"), msg.get("text"))
        if key in seen:
            continue
        seen.add(key)
        result.append(msg)
    return result

def parse_claude_jsonl(jsonl_path):
    """Parse Claude Code session JSONL → structured dict."""
    messages   = []
    tool_calls = []
    first_ts = last_ts = branch = cwd = session_id = model = base_commit = None

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")
            ts = entry.get("timestamp")
            if ts:
                first_ts = first_ts or ts
                last_ts  = ts

            branch     = branch or entry.get("gitBranch")
            cwd        = cwd    or entry.get("cwd") or entry.get("workingDirectory")
            session_id = session_id or entry.get("sessionId")
            base_commit = base_commit or entry.get("gitCommit") or entry.get("gitCommitHash")

            msg  = entry.get("message", {})
            role = msg.get("role")
            if not role or entry_type in ("queue-operation", "file-history-snapshot"):
                continue

            content    = msg.get("content", "")
            text_parts = []

            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    ctype = c.get("type")
                    if ctype == "text":
                        text_parts.append(c.get("text", ""))
                    elif ctype == "tool_use":
                        tool_calls.append({
                            "tool":      c.get("name", ""),
                            "input":     c.get("input", {}),
                            "timestamp": ts,
                        })

            text = "\n".join(text_parts).strip()
            if text:
                messages.append({"role": role, "text": text, "timestamp": ts})

    return {
        "session_id":  session_id or Path(jsonl_path).stem,
        "jsonl_path":  str(jsonl_path),
        "first_ts":    first_ts,
        "last_ts":     last_ts,
        "branch":      branch,
        "cwd":         cwd,
        "base_commit": base_commit,
        "agent_family": "claude",
        "model":       model,
        "messages":    messages,
        "tool_calls":  tool_calls,
    }

def parse_codex_jsonl(jsonl_path):
    """Parse Codex session JSONL → structured dict."""
    event_messages = []
    response_messages = []
    tool_calls = []
    first_ts = last_ts = branch = cwd = session_id = model = base_commit = None

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")
            payload = entry.get("payload") or {}
            ts = entry.get("timestamp")
            if ts:
                first_ts = first_ts or ts
                last_ts = ts

            if entry_type == "session_meta":
                session_id = session_id or payload.get("id")
                cwd = cwd or payload.get("cwd")
                git = payload.get("git") or {}
                branch = branch or git.get("branch")
                base_commit = base_commit or git.get("commit_hash") or git.get("commit")
            elif entry_type == "turn_context":
                cwd = cwd or payload.get("cwd")
                model = model or payload.get("model")
            elif entry_type == "event_msg":
                payload_type = payload.get("type")
                if payload_type == "user_message":
                    text = (payload.get("message") or "").strip()
                    if text:
                        event_messages.append({"role": "user", "text": text, "timestamp": ts})
                elif payload_type == "agent_message":
                    text = (payload.get("message") or "").strip()
                    if text:
                        event_messages.append({"role": "assistant", "text": text, "timestamp": ts})
            elif entry_type == "response_item":
                payload_type = payload.get("type")
                if payload_type == "message":
                    role = payload.get("role")
                    if role in ("user", "assistant"):
                        text = _content_to_text(payload.get("content"))
                        if text:
                            response_messages.append({"role": role, "text": text, "timestamp": ts})
                elif payload_type in ("function_call", "custom_tool_call"):
                    tool_input = payload.get("arguments") if payload_type == "function_call" else payload.get("input")
                    tool_calls.append({
                        "tool": payload.get("name", ""),
                        "input": _parse_tool_input(tool_input),
                        "timestamp": ts,
                    })

    return {
        "session_id": session_id or Path(jsonl_path).stem,
        "jsonl_path": str(jsonl_path),
        "first_ts": first_ts,
        "last_ts": last_ts,
        "branch": branch,
        "cwd": cwd,
        "base_commit": base_commit,
        "agent_family": "codex",
        "model": model,
        "messages": _dedupe_messages(event_messages + response_messages),
        "tool_calls": tool_calls,
    }

def parse_jsonl(jsonl_path):
    fmt = detect_jsonl_format(jsonl_path)
    if fmt == "codex":
        return parse_codex_jsonl(jsonl_path)
    return parse_claude_jsonl(jsonl_path)

# ── Feature extraction ────────────────────────────────────────────────────────

def _detect_command_events(cmd):
    artifacts = []
    for pattern, label in [
        (r'git\s+commit',               "event:commit"),
        (r'git\s+push',                 "event:push"),
        (r'gh\s+pr\s+create',           "event:pr_created"),
        (r'docker.*(build|up|deploy)',  "event:deploy"),
        (r'(pytest|npm\s+test|yarn\s+test|go\s+test|jest|rspec|bash\s+tests?/)', "event:tests"),
    ]:
        if re.search(pattern, cmd):
            artifacts.append({"file_path": label, "action": label, "is_code": 0, "is_doc": 0})
    return artifacts

def _extract_apply_patch_artifacts(patch_text):
    if not patch_text:
        return []
    artifacts = []
    for line in patch_text.splitlines():
        if line.startswith("*** Add File: "):
            artifacts.append((line[len("*** Add File: "):], "created"))
        elif line.startswith("*** Update File: "):
            artifacts.append((line[len("*** Update File: "):], "modified"))
        elif line.startswith("*** Delete File: "):
            artifacts.append((line[len("*** Delete File: "):], "deleted"))
        elif line.startswith("*** Move to: "):
            artifacts.append((line[len("*** Move to: "):], "moved"))
    return artifacts

def extract_artifacts(tool_calls):
    artifacts = []
    seen = set()
    for tc in tool_calls:
        tool = tc["tool"]
        inp  = tc.get("input", {})
        path = action = None

        if tool == "Write":
            path, action = inp.get("file_path"), "created"
        elif tool == "Edit":
            path, action = inp.get("file_path"), "modified"
        elif tool == "Read":
            path, action = inp.get("file_path"), "read"
        elif tool in ("Bash", "exec_command"):
            cmd = inp.get("command") or inp.get("cmd") or inp.get("raw", "")
            artifacts.extend(_detect_command_events(cmd))
        elif tool == "apply_patch":
            patch_text = inp.get("raw", "")
            for patch_path, patch_action in _extract_apply_patch_artifacts(patch_text):
                if patch_path and patch_path not in seen:
                    seen.add(patch_path)
                    ext = Path(patch_path).suffix.lower()
                    artifacts.append({
                        "file_path": patch_path,
                        "action": patch_action,
                        "is_code": int(ext in CODE_EXT),
                        "is_doc": int(ext in DOC_EXT),
                    })

        if path and path not in seen:
            seen.add(path)
            ext = Path(path).suffix.lower()
            artifacts.append({
                "file_path": path,
                "action":    action,
                "is_code":   int(ext in CODE_EXT),
                "is_doc":    int(ext in DOC_EXT),
            })
    return artifacts

def extract_task_ids(messages):
    text = " ".join(m["text"] for m in messages)
    return sorted(set(f"T{n}" for n in re.findall(r'\bT(\d{2,4})\b', text)))

def detect_events(messages, artifacts):
    text = " ".join(m["text"] for m in messages).lower()
    checks = [
        ("handoff_read",   r'handoff'),
        ("changelog_read", r'changelog'),
        ("spec_read",      r'adv-s\d+|specification'),
        ("deploy",         r'deploy|docker.*(up|build)'),
        ("tests_run",      r'pytest|npm test|yarn test|jest|go test'),
        ("commit_made",    r'git commit'),
        ("pr_created",     r'gh pr create|pull request'),
        ("review_done",    r'code review|codereview|ревью'),
        ("task_completed", r'completed|done|завершена'),
    ]
    seen   = set()
    events = []
    for event_type, pattern in checks:
        if event_type not in seen and re.search(pattern, text):
            seen.add(event_type)
            events.append({"event_type": event_type, "detail": None})
    for a in artifacts:
        label_map = {
            "event:commit":     "commit_made",
            "event:push":       "push_made",
            "event:deploy":     "deploy",
            "event:tests":      "tests_run",
            "event:pr_created": "pr_created",
        }
        if a["action"] in label_map and label_map[a["action"]] not in seen:
            seen.add(label_map[a["action"]])
            events.append({"event_type": label_map[a["action"]], "detail": None})
    return events

def detect_domains(messages, artifacts):
    text = " ".join(m["text"] for m in messages).lower()
    checks = [
        ("frontend",     r'\.tsx?|\.jsx?|react|vue|svelte|css|tailwind|component|ui'),
        ("backend",      r'api|server|endpoint|fastapi|django|express|flask|node'),
        ("database",     r'sql|postgres|mysql|mongo|redis|migration|orm'),
        ("tests",        r'\btest\b|spec|pytest|jest|coverage'),
        ("ci_cd",        r'\bci\b|\bcd\b|github.actions|deploy|docker|pipeline'),
        ("docs",         r'\.md|readme|changelog|specification|handoff'),
        ("review",       r'code.review|ревью|finding|critique'),
        ("architecture", r'architecture|design|schema|diagram|structure'),
        ("autodev",      r'autodev|run\.sh|next_v2|handoff|adv-'),
    ]
    domains = []
    file_text = " ".join(a["file_path"] for a in artifacts).lower()
    for domain, pattern in checks:
        if re.search(pattern, text) or re.search(pattern, file_text):
            domains.append(domain)
    return domains

def extract_spec_ids(messages):
    text = " ".join(m["text"] for m in messages)
    return sorted(set(re.findall(r'\b[A-Z]{2,}-S\d+\b', text)))

def _collapse_ws(text):
    return re.sub(r'\s+', ' ', (text or '')).strip()

def _truncate(text, limit):
    text = _collapse_ws(text)
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + "…"

def _extract_request_text(text):
    markers = [
        "## My request for Codex:",
        "My request for Codex:",
        "## My request:",
        "My request:",
        "Запрос:",
        "Мой запрос:",
    ]
    for marker in markers:
        if marker in text:
            return text.split(marker, 1)[1].strip()
    return text

def _extract_skill_invocation_name(text):
    text = _collapse_ws(text)
    match = re.match(r'^\[\$?([a-z][a-z0-9-]*)\]\([^)]+\)$', text, re.I)
    if match:
        return match.group(1).lower()
    match = re.match(r'^\$([a-z][a-z0-9-]*)$', text, re.I)
    if match:
        return match.group(1).lower()
    return None

def _extract_skill_block_info(text):
    if "<skill>" not in (text or ""):
        return None, None
    name_match = re.search(r'<name>\s*([^<]+?)\s*</name>', text, re.I)
    desc_match = re.search(r'^\s*description:\s*(.+)$', text, re.I | re.M)
    skill_name = name_match.group(1).strip().lower() if name_match else None
    description = desc_match.group(1).strip() if desc_match else None
    return skill_name, description

def _is_meta_request(text):
    low = _collapse_ws(text).lower()
    skip_patterns = [
        "# agents.md instructions",
        "<instructions>",
        "<environment_context>",
        "<skill>",
    ]
    return any(pattern in low for pattern in skip_patterns)

def _select_goal(messages):
    user_messages = [m for m in messages if m.get("role") == "user" and m.get("text")]
    for idx, msg in enumerate(user_messages):
        request = _extract_request_text(msg["text"])
        if not request or _is_meta_request(request):
            continue

        skill_name = _extract_skill_invocation_name(request)
        if skill_name and idx + 1 < len(user_messages):
            next_name, next_desc = _extract_skill_block_info(user_messages[idx + 1].get("text", ""))
            if next_name == skill_name and next_desc:
                return next_desc

        return request
    return ""

def detect_skills_used(messages, tool_calls, agent_family):
    text = "\n".join(m["text"] for m in messages)
    found = set()

    if agent_family == "claude":
        found.update(re.findall(r'<command-name>/?([a-z][a-z0-9-]+)</command-name>', text))
        found.update(re.findall(r'(?<!\w)/([a-z][a-z0-9-]+)', " ".join(m["text"] for m in messages if m["role"] == "user")))

    for tc in tool_calls:
        blob = json.dumps(tc.get("input", {}), ensure_ascii=False)
        found.update(re.findall(r'/\.codex/skills/([^/\s]+)/SKILL\.md', blob))
        found.update(re.findall(r'/\.claude/commands/([a-z0-9-]+)\.md', blob))

    return sorted(s for s in found if s not in ("archive-session", "session-archive"))

def extract_open_issues(messages):
    patterns = [
        "open issue", "open issues", "follow-up", "follow up", "blocker",
        "not run", "did not run", "remaining", "left unfinished",
        "не запускал", "не запускались", "не выполнен", "не выполнено",
        "осталось", "блокер", "followup",
    ]
    issues = []
    seen = set()

    for msg in reversed(messages[-8:]):
        if msg.get("role") != "assistant":
            continue
        for raw_line in msg.get("text", "").splitlines():
            line = raw_line.strip().lstrip("-* ").strip()
            low = line.lower()
            if not line:
                continue
            if any(pattern in low for pattern in patterns):
                clean = _truncate(line, 240)
                if clean not in seen:
                    seen.add(clean)
                    issues.append(clean)

    return list(reversed(issues))

def infer_task_action(messages_text, task_id):
    windows = []
    task_id_low = task_id.lower()
    for match in re.finditer(re.escape(task_id_low), messages_text):
        start = max(0, match.start() - 160)
        end = min(len(messages_text), match.end() + 160)
        windows.append(messages_text[start:end])
    context = " ".join(windows) or messages_text
    if re.search(r'review|reviewed|codereview|ревью|finding', context):
        return "reviewed"
    if re.search(r'implement|implemented|fix|fixed|patched|updated|changed|внес|исправ|добавил|обновил', context):
        return "implemented"
    return "mentioned"

def detect_repo_name(project_path):
    project_path = project_path or os.getcwd()
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        remote = (result.stdout or "").strip()
        if remote:
            match = re.search(r'([^/:]+?)(?:\.git)?$', remote)
            if match:
                return match.group(1)
    except Exception:
        pass
    return Path(project_path).name

def detect_git_branch(project_path):
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        branch = (result.stdout or "").strip()
        if branch:
            return branch
    except Exception:
        pass
    return ""

def detect_git_root(project_path):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        root = (result.stdout or "").strip()
        if root:
            return str(Path(root).resolve())
    except Exception:
        pass
    return None

def _normalize_artifact_key(project_root, file_path):
    file_path = (file_path or "").strip()
    if not file_path or file_path.startswith("event:"):
        return file_path

    candidate = Path(file_path).expanduser()
    if candidate.is_absolute():
        try:
            if project_root:
                return str(candidate.resolve().relative_to(project_root))
        except Exception:
            return str(candidate.resolve())
        return str(candidate.resolve())

    return file_path

def _resolve_artifact_path(project_root, file_path):
    file_path = (file_path or "").strip()
    if not file_path or file_path.startswith("event:"):
        return None

    candidate = Path(file_path).expanduser()
    if candidate.is_absolute():
        return candidate
    if project_root:
        return Path(project_root) / candidate
    return candidate

def _read_text_file(path_obj):
    if not path_obj:
        return None
    try:
        return Path(path_obj).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

def _truncate_diff_text(diff_text, limit=MAX_ARTIFACT_DIFF):
    if not diff_text:
        return diff_text
    if len(diff_text) <= limit:
        return diff_text
    clipped = diff_text[:limit].rstrip()
    return clipped + "\n... [diff truncated]\n"

def _run_git(project_root, args):
    if not project_root:
        return ""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout or ""

def _build_unified_diff(file_path, before_text, after_text):
    before_lines = (before_text or "").splitlines(keepends=True)
    after_lines = (after_text or "").splitlines(keepends=True)
    diff_lines = unified_diff(
        before_lines,
        after_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
    )
    return "\n".join(diff_lines).strip()

def _extract_apply_patch_diffs(patch_text):
    if not patch_text:
        return {}

    result = {}
    current_path = None
    current_lines = []

    def flush():
        nonlocal current_path, current_lines
        if current_path and current_lines:
            result[current_path] = "\n".join(current_lines).strip()
        current_path = None
        current_lines = []

    for raw_line in patch_text.splitlines():
        if raw_line.startswith("*** Begin Patch") or raw_line.startswith("*** End Patch"):
            continue
        if raw_line.startswith("*** Add File: "):
            flush()
            current_path = raw_line[len("*** Add File: "):].strip()
        elif raw_line.startswith("*** Update File: "):
            flush()
            current_path = raw_line[len("*** Update File: "):].strip()
        elif raw_line.startswith("*** Delete File: "):
            flush()
            current_path = raw_line[len("*** Delete File: "):].strip()
        elif raw_line.startswith("*** Move to: "):
            current_lines.append(raw_line)
        elif current_path:
            current_lines.append(raw_line)

    flush()
    return result

def _collect_tool_diff_hints(tool_calls, project_root):
    hints = {}

    def remember(path_key, diff_text, source):
        if not path_key or not diff_text or path_key in hints:
            return
        hints[path_key] = {
            "diff": _truncate_diff_text(diff_text),
            "diff_source": source,
        }

    for tc in tool_calls:
        tool = tc.get("tool")
        inp = tc.get("input", {}) or {}

        if tool == "apply_patch":
            for path, patch_diff in _extract_apply_patch_diffs(inp.get("raw", "")).items():
                remember(_normalize_artifact_key(project_root, path), patch_diff, "apply_patch")
            continue

        if tool == "Edit":
            file_path = inp.get("file_path")
            old_string = inp.get("old_string")
            new_string = inp.get("new_string")
            if file_path and old_string is not None and new_string is not None:
                remember(
                    _normalize_artifact_key(project_root, file_path),
                    _build_unified_diff(file_path, old_string, new_string),
                    "edit_snippet",
                )
            continue

        if tool == "MultiEdit":
            file_path = inp.get("file_path")
            edits = inp.get("edits") or []
            if not file_path or not isinstance(edits, list):
                continue
            snippets = []
            for idx, edit in enumerate(edits, start=1):
                old_string = (edit or {}).get("old_string")
                new_string = (edit or {}).get("new_string")
                if old_string is None or new_string is None:
                    continue
                snippet = _build_unified_diff(f"{file_path}#edit{idx}", old_string, new_string)
                if snippet:
                    snippets.append(snippet)
            if snippets:
                remember(
                    _normalize_artifact_key(project_root, file_path),
                    "\n\n".join(snippets),
                    "multiedit_snippet",
                )
            continue

        if tool == "Write":
            file_path = inp.get("file_path")
            content = inp.get("content")
            if not file_path or content is None:
                continue
            remember(
                _normalize_artifact_key(project_root, file_path),
                _build_unified_diff(file_path, "", content),
                "write_snapshot",
            )

    return hints

def _git_diff_for_artifact(project_root, base_commit, rel_path):
    if not project_root or not rel_path:
        return None, None

    diff_text = ""
    source = None
    if base_commit:
        diff_text = _run_git(
            project_root,
            ["diff", "--no-ext-diff", "--find-renames", "--binary", "--relative", base_commit, "--", rel_path],
        )
        if diff_text.strip():
            source = "git_base"

    if not diff_text.strip():
        diff_text = _run_git(
            project_root,
            ["diff", "--no-ext-diff", "--find-renames", "--binary", "--relative", "HEAD", "--", rel_path],
        )
        if diff_text.strip():
            source = "git_head"

    if not diff_text.strip():
        return None, None
    return _truncate_diff_text(diff_text.strip()), source

def _synthetic_diff_for_artifact(project_root, rel_path, path_obj, action):
    if not rel_path or not path_obj:
        return None

    current_text = _read_text_file(path_obj)
    if current_text is None and action != "deleted":
        return None

    before_text = None
    if project_root:
        before_text = _run_git(project_root, ["show", f"HEAD:{rel_path}"])
        if before_text == "":
            ls = _run_git(project_root, ["ls-files", "--error-unmatch", rel_path])
            if not ls.strip():
                before_text = None

    if action == "deleted":
        if before_text is None:
            return None
        return _truncate_diff_text(_build_unified_diff(rel_path, before_text, ""))

    if before_text is None:
        return _truncate_diff_text(_build_unified_diff(rel_path, "", current_text or ""))

    if before_text == current_text:
        return None
    return _truncate_diff_text(_build_unified_diff(rel_path, before_text, current_text or ""))

def _resolve_artifact_diff(item, project_root, base_commit, tool_diff_hints):
    rel_path = _normalize_artifact_key(project_root, item.get("file_path"))
    if not rel_path or rel_path.startswith("event:"):
        return None, None

    diff_text, diff_source = _git_diff_for_artifact(project_root, base_commit, rel_path)
    if diff_text:
        return diff_text, diff_source

    hint = tool_diff_hints.get(rel_path)
    if hint:
        return hint.get("diff"), hint.get("diff_source")

    path_obj = _resolve_artifact_path(project_root, item.get("file_path"))
    diff_text = _synthetic_diff_for_artifact(project_root, rel_path, path_obj, item.get("action"))
    if diff_text:
        return diff_text, "synthetic"

    return None, None

def enrich_artifacts(artifacts, project_path, tool_calls=None, base_commit=None):
    project_root = detect_git_root(project_path) or project_path
    project_root = str(Path(project_root).resolve()) if project_root else None
    tool_diff_hints = _collect_tool_diff_hints(tool_calls or [], project_root)
    enriched = []
    for artifact in artifacts:
        item = dict(artifact)
        file_path = item.get("file_path") or ""
        action = item.get("action")
        if action in ("created", "modified") and file_path and not file_path.startswith("event:"):
            content = _read_text_file(_resolve_artifact_path(project_root, file_path))
            item["content"] = content[:MAX_ARTIFACT_CONTENT] if content is not None else None
        if action in DIFF_ACTIONS and file_path and not file_path.startswith("event:"):
            diff_text, diff_source = _resolve_artifact_diff(item, project_root, base_commit, tool_diff_hints)
            item["diff"] = diff_text
            item["diff_source"] = diff_source
        enriched.append(item)
    return enriched

# Patterns that indicate a meta/administrative assistant message (archiving, deploy status, etc.)
# These should be skipped when selecting the "outcome" message for summary.
_OUTCOME_SKIP_PATTERNS = [
    "session_id", "export_path", "agent_family", "jsonl_path",
    "archive-current", "archive_current",
    "session-archive", "навык `session-archive`",
    "сохраню текущую сессию", "путь к экспорту",
    "заархивировать", "архив сессии", "session archive",
]

def _is_meta_outcome(text):
    t = text.lower()
    return any(p in t for p in _OUTCOME_SKIP_PATTERNS)

def build_summary(messages, task_ids, spec_ids, open_issues):
    assistant_messages = [m for m in messages if m.get("role") == "assistant" and m.get("text")]
    parts = []

    goal = _truncate(_select_goal(messages), 220)
    if goal:
        parts.append(f"Goal: {goal}")

    refs = []
    if task_ids:
        refs.append("tasks " + ", ".join(task_ids[:6]))
    if spec_ids:
        refs.append("specs " + ", ".join(spec_ids[:4]))
    if refs:
        parts.append("References: " + "; ".join(refs) + ".")

    if assistant_messages:
        # Walk backwards to find the last substantive (non-meta) message
        outcome_msg = next(
            (m for m in reversed(assistant_messages) if not _is_meta_outcome(m["text"])),
            assistant_messages[-1],  # fallback: use last message if all are meta
        )
        outcome = _truncate(outcome_msg["text"], 480)
        if outcome:
            parts.append(f"Outcome: {outcome}")

    if open_issues:
        parts.append("Open issues: " + "; ".join(open_issues[:3]))

    return _truncate(" ".join(parts), 1400)

def build_parsed_result(data):
    artifacts = extract_artifacts(data["tool_calls"])
    task_ids = extract_task_ids(data["messages"])
    events = detect_events(data["messages"], artifacts)
    domains = detect_domains(data["messages"], artifacts)
    return {
        **{k: v for k, v in data.items() if k not in ("tool_calls",)},
        "agent_family": data.get("agent_family"),
        "ai_model": data.get("model"),
        "msg_count": len(data["messages"]),
        "tool_call_count": len(data["tool_calls"]),
        "user_msg_count": sum(1 for m in data["messages"] if m["role"] == "user"),
        "task_ids": task_ids,
        "events": events,
        "domains": domains,
        "artifacts": artifacts,
    }

def build_metadata(parsed, summary_override=None, model_override=None, cwd_override=None):
    project_path = cwd_override or parsed.get("cwd") or os.getcwd()
    project_path = str(Path(project_path).expanduser().resolve())
    agent_family = infer_agent_family(parsed)
    task_ids = list(parsed.get("task_ids") or [])
    spec_ids = extract_spec_ids(parsed.get("messages", []))
    open_issues = extract_open_issues(parsed.get("messages", []))
    repo_name = detect_repo_name(project_path)
    branch = parsed.get("branch") or detect_git_branch(project_path)
    ai_model = model_override or parsed.get("ai_model") or ("claude" if agent_family == "claude" else "codex")
    skills_used = detect_skills_used(parsed.get("messages", []), parsed.get("tool_calls", []), agent_family)
    tasks_text = " ".join(m["text"] for m in parsed.get("messages", [])).lower()

    tags = [
        {"category": "assistant", "value": agent_family},
        {"category": "project", "value": repo_name},
        {"category": "branch", "value": branch or "unknown"},
        {"category": "model", "value": ai_model},
    ]
    for domain in parsed.get("domains", []):
        tags.append({"category": "domain", "value": domain})
    for skill in skills_used:
        tags.append({"category": "skill", "value": skill})

    tasks = []
    for task_id in task_ids:
        tasks.append({"task_id": task_id, "actions": infer_task_action(tasks_text, task_id)})
    for spec_id in spec_ids:
        tasks.append({"task_id": spec_id, "actions": "referenced"})

    summary = summary_override or build_summary(parsed.get("messages", []), task_ids, spec_ids, open_issues)

    return {
        "session_id": parsed["session_id"],
        "created_at": parsed.get("first_ts"),
        "ended_at": parsed.get("last_ts"),
        "project_path": project_path,
        "repo_name": repo_name,
        "branch": branch,
        "agent_family": agent_family,
        "ai_model": ai_model,
        "base_commit": parsed.get("base_commit"),
        "summary": summary,
        "msg_count": parsed.get("msg_count", 0),
        "user_msg_count": parsed.get("user_msg_count", 0),
        "tool_call_count": parsed.get("tool_call_count", 0),
        "raw_jsonl_path": parsed.get("jsonl_path"),
        "tags": tags,
        "tasks": tasks,
        "artifacts": enrich_artifacts(
            parsed.get("artifacts", []),
            project_path,
            tool_calls=parsed.get("tool_calls", []),
            base_commit=parsed.get("base_commit"),
        ),
        "events": parsed.get("events", []),
        "open_issues": open_issues,
        "messages": parsed.get("messages", []),
    }

def peek_session_header(jsonl_path):
    info = {
        "jsonl_path": str(jsonl_path),
        "session_id": Path(jsonl_path).stem,
        "cwd": None,
        "branch": None,
        "first_ts": None,
        "last_ts": None,
        "agent_family": None,
    }
    with open(jsonl_path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = entry.get("timestamp")
            if ts:
                info["first_ts"] = info["first_ts"] or ts
                info["last_ts"] = ts

            entry_type = entry.get("type", "")
            payload = entry.get("payload") or {}

            if entry_type == "session_meta" and payload.get("originator", "").startswith("codex"):
                info["agent_family"] = "codex"
                info["session_id"] = payload.get("id") or info["session_id"]
                info["cwd"] = info["cwd"] or payload.get("cwd")
                git = payload.get("git") or {}
                info["branch"] = info["branch"] or git.get("branch")
            else:
                info["session_id"] = info["session_id"] or entry.get("sessionId")
                info["cwd"] = info["cwd"] or entry.get("cwd") or entry.get("workingDirectory")
                info["branch"] = info["branch"] or entry.get("gitBranch")
                if info["cwd"] or info["branch"] or entry.get("message") is not None:
                    info["agent_family"] = info["agent_family"] or "claude"

            if info["cwd"] and info["agent_family"] and idx >= 8:
                break
    return info

def iter_session_jsonl_paths(agent_family):
    roots = []
    home = Path.home()
    if agent_family in ("auto", "claude"):
        roots.append(home / ".claude" / "projects")
    if agent_family in ("auto", "codex"):
        roots.append(home / ".codex" / "sessions")

    for root in roots:
        if root.exists():
            for path in root.rglob("*.jsonl"):
                yield path

def find_current_jsonl(cwd=None, agent_family="auto"):
    target_cwd = str(Path(cwd or os.getcwd()).expanduser().resolve())
    basename = Path(target_cwd).name
    exact = []
    fuzzy = []

    for path in iter_session_jsonl_paths(agent_family):
        info = peek_session_header(path)
        candidate_cwd = info.get("cwd")
        if candidate_cwd:
            try:
                candidate_cwd = str(Path(candidate_cwd).expanduser().resolve())
            except Exception:
                candidate_cwd = str(candidate_cwd)
        score = (
            info.get("first_ts") or "",
            info.get("last_ts") or "",
            path.stat().st_mtime,
            str(path),
        )
        if candidate_cwd == target_cwd:
            exact.append((score, info))
        elif candidate_cwd and Path(candidate_cwd).name == basename:
            fuzzy.append((score, info))

    pool = exact or fuzzy
    if not pool:
        raise FileNotFoundError(f"No session JSONL found for cwd={target_cwd} agent={agent_family}")

    pool.sort(key=lambda item: item[0], reverse=True)
    return pool[0][1]

# ── DB write ──────────────────────────────────────────────────────────────────

def write_session(metadata: dict) -> str:
    conn = get_db()
    sid = metadata["session_id"]
    agent_family = infer_agent_family(metadata)

    open_issues = metadata.get("open_issues")
    if isinstance(open_issues, list):
        open_issues = json.dumps(open_issues, ensure_ascii=False)

    tags = list(metadata.get("tags", []))
    if not any(tag.get("category") == "assistant" for tag in tags):
        tags.append({"category": "assistant", "value": agent_family})

    conn.execute("""
        INSERT OR REPLACE INTO sessions
          (id, created_at, ended_at, project_path, repo_name, branch, base_commit, agent_family,
           ai_model, summary, open_issues, msg_count, user_msg_count, tool_call_count,
           export_path, raw_jsonl_path)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        sid,
        metadata.get("created_at") or datetime.now(timezone.utc).isoformat(),
        metadata.get("ended_at"),
        metadata.get("project_path", ""),
        metadata.get("repo_name", ""),
        metadata.get("branch", ""),
        metadata.get("base_commit", ""),
        agent_family,
        metadata.get("ai_model", "claude"),
        metadata.get("summary", ""),
        open_issues,
        metadata.get("msg_count", 0),
        metadata.get("user_msg_count", 0),
        metadata.get("tool_call_count", 0),
        metadata.get("export_path", ""),
        metadata.get("raw_jsonl_path", ""),
    ))

    for tbl in ("session_tags", "session_tasks", "session_artifacts", "session_events", "session_messages"):
        conn.execute(f"DELETE FROM {tbl} WHERE session_id=?", (sid,))

    for tag in tags:
        conn.execute("INSERT INTO session_tags (session_id, category, value) VALUES (?,?,?)",
                     (sid, tag["category"], tag["value"]))
    for task in metadata.get("tasks", []):
        conn.execute("INSERT INTO session_tasks (session_id, task_id, actions) VALUES (?,?,?)",
                     (sid, task["task_id"], task.get("actions", "")))
    for a in metadata.get("artifacts", []):
        conn.execute("""INSERT INTO session_artifacts
            (session_id, file_path, action, is_code, is_doc, content, diff, diff_source)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                sid,
                a["file_path"],
                a.get("action"),
                a.get("is_code", 0),
                a.get("is_doc", 0),
                a.get("content"),
                a.get("diff"),
                a.get("diff_source"),
            ))
    for e in metadata.get("events", []):
        conn.execute("INSERT INTO session_events (session_id, event_type, detail) VALUES (?,?,?)",
                     (sid, e["event_type"], e.get("detail")))

    for m in metadata.get("messages", []):
        conn.execute("INSERT INTO session_messages (session_id, role, text, timestamp) VALUES (?,?,?,?)",
                     (sid, m.get("role", ""), m.get("text", ""), m.get("timestamp")))

    conn.commit()
    conn.close()
    return sid

# ── Export markdown ───────────────────────────────────────────────────────────

def export_markdown(session_id, messages, metadata) -> str:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = (metadata.get("created_at") or "")[:10] or datetime.now().strftime("%Y-%m-%d")
    repo     = re.sub(r'[^a-zA-Z0-9_-]', '', metadata.get("repo_name", "unknown"))
    agent_family = infer_agent_family(metadata)
    agent_label = display_agent_family(agent_family)
    path     = EXPORT_DIR / f"{date_str}_{repo}_{agent_family}_{session_id[:8]}.md"

    lines = [
        f"# {agent_label} Session {session_id[:8]}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Date | {metadata.get('created_at', '')[:19]} |",
        f"| Assistant | {agent_label} |",
        f"| Project | `{metadata.get('project_path', '')}` |",
        f"| Repo | {metadata.get('repo_name', '')} |",
        f"| Branch | {metadata.get('branch', '')} |",
        f"| Base commit | {metadata.get('base_commit', '') or '-'} |",
        f"| Model | {metadata.get('ai_model', '')} |",
        f"| Messages | {metadata.get('msg_count', 0)} |",
        f"| Tool calls | {metadata.get('tool_call_count', 0)} |",
        "",
        "## Summary",
        "",
        metadata.get("summary", ""),
        "",
        "## Tags",
        "",
    ]
    for tag in metadata.get("tags", []):
        lines.append(f"- **{tag['category']}:** {tag['value']}")
    open_issues = metadata.get("open_issues") or []
    if isinstance(open_issues, str):
        try:
            open_issues = json.loads(open_issues)
        except Exception:
            open_issues = [open_issues]
    if open_issues:
        lines += ["", "## Open Issues", ""]
        for issue in open_issues:
            lines.append(f"- {issue}")

    lines += ["", "## Events", ""]
    for e in metadata.get("events", []):
        lines.append(f"- {e['event_type']}")
    lines += ["", "## Tasks", ""]
    for t in metadata.get("tasks", []):
        lines.append(f"- {t['task_id']}")
    lines += ["", "## Artifacts", ""]
    for a in metadata.get("artifacts", []):
        if not a["file_path"].startswith("event:"):
            lines.append(f"- `{a['file_path']}` ({a.get('action', '?')})")

    diff_artifacts = [
        a for a in metadata.get("artifacts", [])
        if a.get("diff") and not a.get("file_path", "").startswith("event:")
    ]
    if diff_artifacts:
        lines += ["", "## Diffs", ""]
        for artifact in diff_artifacts:
            source = artifact.get("diff_source") or "unknown"
            lines.append(f"### `{artifact['file_path']}` ({source})")
            lines.append("")
            lines.append("```diff")
            lines.append((artifact.get("diff") or "").rstrip())
            lines.append("```")
            lines.append("")

    lines += ["", "---", "", "## Transcript", ""]

    for msg in messages:
        role = msg["role"].upper()
        ts   = (msg.get("timestamp") or "")[:19]
        text = msg.get("text", "").strip()
        if not text:
            continue
        lines.append(f"### {role} [{ts}]")
        lines.append("")
        lines.append(text)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)

# ── Stats ─────────────────────────────────────────────────────────────────────

def print_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    print(f"\n=== Session Archive — {total} sessions ===\n")
    rows = conn.execute("""
        SELECT s.id, s.created_at, s.repo_name, s.branch, s.agent_family,
               s.msg_count, s.tool_call_count,
               GROUP_CONCAT(DISTINCT st.task_id) as tasks,
               GROUP_CONCAT(DISTINCT se.event_type) as events
        FROM sessions s
        LEFT JOIN session_tasks st  ON st.session_id  = s.id
        LEFT JOIN session_events se ON se.session_id  = s.id
        GROUP BY s.id
        ORDER BY s.created_at DESC
        LIMIT 30
    """).fetchall()
    for r in rows:
        agent_label = display_agent_family(r["agent_family"])
        print(
            f"{r['created_at'][:16]}  "
            f"{agent_label:7s}  "
            f"{(r['repo_name'] or '?'):18s}  "
            f"br={r['branch'] or '?':12s}  "
            f"msgs={r['msg_count']:3d}  tools={r['tool_call_count']:3d}  "
            f"tasks={r['tasks'] or '-':12s}  "
            f"events={r['events'] or '-'}"
        )
    conn.close()

# ── CLI ───────────────────────────────────────────────────────────────────────

def cmd_parse(jsonl_path):
    data = parse_jsonl(jsonl_path)
    result = build_parsed_result(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def parse_archive_current_args(argv):
    opts = {
        "agent": "auto",
        "cwd": os.getcwd(),
        "summary": None,
        "model": None,
        "jsonl": None,
    }
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--help":
            print(__doc__)
            sys.exit(0)
        if "=" in arg and arg.startswith("--"):
            key, value = arg.split("=", 1)
        else:
            key, value = arg, None

        if key in ("--agent", "--cwd", "--summary", "--model", "--jsonl"):
            if value is None:
                if i + 1 >= len(argv):
                    raise SystemExit(f"Missing value for {key}")
                value = argv[i + 1]
                i += 2
            else:
                i += 1

            if key == "--agent":
                opts["agent"] = value
            elif key == "--cwd":
                opts["cwd"] = value
            elif key == "--summary":
                opts["summary"] = value
            elif key == "--model":
                opts["model"] = value
            elif key == "--jsonl":
                opts["jsonl"] = value
            continue

        raise SystemExit(f"Unknown argument: {arg}")

    return opts

def cmd_archive_current(argv):
    opts = parse_archive_current_args(argv)

    if opts["jsonl"]:
        session_info = {"jsonl_path": str(Path(opts["jsonl"]).expanduser())}
    else:
        session_info = find_current_jsonl(cwd=opts["cwd"], agent_family=opts["agent"])

    data = parse_jsonl(session_info["jsonl_path"])
    parsed = build_parsed_result(data)
    parsed["tool_calls"] = data.get("tool_calls", [])
    metadata = build_metadata(
        parsed,
        summary_override=opts["summary"],
        model_override=opts["model"],
        cwd_override=opts["cwd"],
    )

    messages = metadata.get("messages", [])
    lock_path = DB_PATH.parent / ".archive.lock"
    with open(lock_path, "w") as _lf:
        fcntl.flock(_lf, fcntl.LOCK_EX)
        sid = write_session(metadata)
        export_path = export_markdown(sid, messages, metadata)
        conn = get_db()
        conn.execute("UPDATE sessions SET export_path=? WHERE id=?", (export_path, sid))
        conn.commit()
        conn.close()

    print(json.dumps({
        "session_id": sid,
        "agent_family": metadata.get("agent_family"),
        "ai_model": metadata.get("ai_model"),
        "repo_name": metadata.get("repo_name"),
        "branch": metadata.get("branch"),
        "jsonl_path": session_info["jsonl_path"],
        "export_path": export_path,
    }, ensure_ascii=False))

def cmd_write(metadata_json_file):
    with open(metadata_json_file, encoding="utf-8") as f:
        metadata = json.load(f)
    messages = metadata.get("messages", [])          # keep in metadata for write_session
    metadata["agent_family"] = infer_agent_family(metadata)
    sid      = write_session(metadata)
    metadata.pop("messages", None)                   # remove before export
    ep       = export_markdown(sid, messages, metadata)
    conn     = get_db()
    conn.execute("UPDATE sessions SET export_path=? WHERE id=?", (ep, sid))
    conn.commit()
    conn.close()
    print(json.dumps({
        "session_id": sid,
        "agent_family": metadata.get("agent_family"),
        "export_path": ep,
    }, ensure_ascii=False))

def cmd_query(sql):
    conn = get_db()
    rows = conn.execute(sql).fetchall()
    print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if   cmd == "parse" and len(sys.argv) >= 3: cmd_parse(sys.argv[2])
    elif cmd == "write" and len(sys.argv) >= 3: cmd_write(sys.argv[2])
    elif cmd == "archive-current":              cmd_archive_current(sys.argv[2:])
    elif cmd == "stats":                         print_stats()
    elif cmd == "query" and len(sys.argv) >= 3: cmd_query(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)
