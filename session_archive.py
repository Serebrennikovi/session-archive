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
SYNTHETIC_DIFF_MAX_LINES = 300   # untracked files larger than this get diff_source='manual'
SYNTHETIC_DIFF_MAX_BYTES = 200_000  # files larger than this get diff_source='manual'

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
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
    # UNIQUE constraints to prevent duplicates on repeated archive runs.
    # Each block deduplicates existing rows first (BUG-UNIQUE-INDEX-SILENT-FAIL).
    for idx_name, table, cols, group_cols in [
        ("idx_session_tags_unique",   "session_tags",   "session_id, category, value", "session_id, category, value"),
        ("idx_session_tasks_unique",  "session_tasks",  "session_id, task_id",         "session_id, task_id"),
        ("idx_session_events_unique", "session_events", "session_id, event_type",      "session_id, event_type"),
    ]:
        if not conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?", (idx_name,)
        ).fetchone():
            conn.execute(f"""
                DELETE FROM {table}
                WHERE id NOT IN (SELECT MAX(id) FROM {table} GROUP BY {group_cols})
            """)
            conn.execute(f"CREATE UNIQUE INDEX {idx_name} ON {table}({cols})")
    # Cleanup before creating unique index on session_artifacts:
    # 1. Remove event:* pseudo-artifacts that should never be in this table (BUG-ARTIFACT-EVENT-PSEUDO)
    # 2. Deduplicate (session_id, file_path) keeping the row with most data (highest id)
    existing_idx = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_session_artifacts_unique'"
    ).fetchone()
    if not existing_idx:
        conn.execute("DELETE FROM session_artifacts WHERE file_path LIKE 'event:%'")
        conn.execute("""
            DELETE FROM session_artifacts
            WHERE id NOT IN (
                SELECT MAX(id) FROM session_artifacts GROUP BY session_id, file_path
            )
        """)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_session_artifacts_unique "
            "ON session_artifacts(session_id, file_path)"
        )
    _ensure_column(conn, "sessions", "agent_family", "TEXT DEFAULT 'unknown'")
    _ensure_column(conn, "sessions", "base_commit", "TEXT")
    _ensure_column(conn, "sessions", "summary_manual", "TEXT")
    _ensure_column(conn, "sessions", "manually_reviewed", "INTEGER DEFAULT 0")
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

def _dedupe_adjacent_messages(messages):
    """Удалить соседние дубли (role, text) из списка сообщений."""
    if not messages:
        return messages
    deduped = [messages[0]]
    for msg in messages[1:]:
        prev = deduped[-1]
        if msg.get("role") == prev.get("role") and msg.get("text") == prev.get("text"):
            continue
        deduped.append(msg)
    return deduped

_CATN_RE = re.compile(r"^\s*\d+\u2192", re.MULTILINE)
_SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
_INJECTED_CONTEXT_RE = re.compile(
    r"<(?:system-reminder|ide_opened_file|ide_selection|user-prompt-submit-hook)>.*?"
    r"</(?:system-reminder|ide_opened_file|ide_selection|user-prompt-submit-hook)>",
    re.DOTALL,
)

def _strip_read_tool_formatting(text):
    """Strip cat-n line-number prefixes and system-reminder blocks from Read tool output."""
    text = _SYSTEM_REMINDER_RE.sub("", text)
    text = _CATN_RE.sub("", text)
    return text

def _build_read_snapshots(tool_calls, tool_use_ids, tool_results):
    """Build {file_path: raw_content} from Read tool results.

    Only includes full-file reads (no offset/limit) to avoid partial-content snapshots
    that would produce misleading diffs.
    """
    snapshots = {}
    for tu_id, idx in tool_use_ids.items():
        tc = tool_calls[idx]
        if tc["tool"] != "Read":
            continue
        inp = tc.get("input") or {}
        fp = inp.get("file_path", "")
        if not fp:
            continue
        # Skip partial reads (offset/limit specified) — partial content ≠ full baseline
        if inp.get("offset") or inp.get("limit"):
            continue
        if tu_id not in tool_results:
            continue
        raw = tool_results[tu_id]
        if not raw:
            continue
        snapshots[fp] = _strip_read_tool_formatting(raw)
    return snapshots


def parse_claude_jsonl(jsonl_path, tool_id_whitelist=None):
    """Parse Claude Code session JSONL → structured dict.

    tool_id_whitelist: set of tool_call_ids observed in the context window.
    When provided (non-empty), only tool_use entries whose id is in the set
    are included — this prevents cross-session contamination when multiple
    sessions share the same JSONL file.
    """
    messages   = []
    tool_calls = []
    _tool_use_ids  = {}  # tool_use id → index in tool_calls
    _tool_results  = {}  # tool_use_id → result text
    _tool_errors   = {}  # tool_use_id → bool (is_error)
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
            entry_session_id = entry.get("sessionId")
            session_id = session_id or entry_session_id
            base_commit = base_commit or entry.get("gitCommit") or entry.get("gitCommitHash")

            # Skip entries from other sessions to avoid cross-session artifact contamination.
            # Only filter once session_id is determined and entry has an explicit sessionId.
            if session_id and entry_session_id and entry_session_id != session_id:
                continue

            msg  = entry.get("message", {})
            role = msg.get("role")
            if not role or entry_type in ("queue-operation", "file-history-snapshot"):
                continue

            if role == "assistant":
                model = model or msg.get("model") or entry.get("model")

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
                        tc_id = c.get("id")
                        if tool_id_whitelist is not None and tc_id not in tool_id_whitelist:
                            continue  # cross-session tool call — skip
                        if tc_id:
                            _tool_use_ids[tc_id] = len(tool_calls)
                        tool_calls.append({
                            "tool":      c.get("name", ""),
                            "input":     c.get("input", {}),
                            "timestamp": ts,
                            "id":        tc_id,
                        })
                    elif ctype == "tool_result":
                        tu_id = c.get("tool_use_id")
                        if tu_id:
                            _tool_errors[tu_id] = bool(c.get("is_error"))
                            rc = c.get("content")
                            if isinstance(rc, str):
                                _tool_results[tu_id] = rc
                            elif isinstance(rc, list):
                                _tool_results[tu_id] = "\n".join(
                                    item.get("text", "") for item in rc
                                    if isinstance(item, dict) and item.get("type") == "text"
                                )

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
        "messages":    _dedupe_adjacent_messages(messages),
        "tool_calls":     tool_calls,
        "tool_errors":    _tool_errors,
        "read_snapshots": _build_read_snapshots(tool_calls, _tool_use_ids, _tool_results),
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

def parse_jsonl(jsonl_path, tool_id_whitelist=None):
    fmt = detect_jsonl_format(jsonl_path)
    if fmt == "codex":
        return parse_codex_jsonl(jsonl_path)
    return parse_claude_jsonl(jsonl_path, tool_id_whitelist=tool_id_whitelist)

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

# Paths that are never project files (skip from shell-read trace)
_SHELL_READ_SYSTEM_PREFIXES = ("/usr/", "/bin/", "/sbin/", "/lib/", "/etc/", "/tmp/",
                                "/proc/", "/sys/", "/dev/", "/var/", "/opt/")

# Patterns to extract file paths from shell read commands in Bash tool calls (SA-T033)
_SHELL_READ_PATTERNS = [
    # sed [-n] 'Xp' /path  or  sed -n 'X,Yp' /path
    r"\bsed\s+(?:-[nEi]\s+)*(?:'[^']*'|\"[^\"]*\")\s+([^\s|>&;\"']+)",
    # cat /path/to/file
    r"\bcat\s+([^\s|>&;\"']+)",
    # nl /path/to/file
    r"\bnl\s+([^\s|>&;\"']+)",
    # head/tail -n N /path  or  head/tail /path
    r"\b(?:head|tail)\s+(?:-[nfq]\s+\d+\s+)?([^\s|>&;\"'-][^\s|>&;\"']*)",
    # rg/grep pattern /path -- only pick up paths with extension or slash
    r"\b(?:rg|grep)\s+(?:-[^\s]+\s+)*(?:\"[^\"]+\"|'[^']+'|\S+)\s+([^\s|>&;\"']+\.(?:py|go|js|jsx|ts|tsx|md|yaml|yml|json|toml|sql|sh|txt|cfg|conf|mod|sum|lock))",
    # git diff HEAD -- /path  or  git show HEAD:file
    r"\bgit\s+(?:diff|show)\s+[^\s]+\s+(?:--\s+)?([^\s|>&;\"']+)",
    # git log [--] /path
    r"\bgit\s+log\s+.*?--\s+([^\s|>&;\"']+)",
    # sqlite3 /path/to/db
    r"\bsqlite3\s+([^\s\"']+\.(?:db|sqlite|sqlite3))",
]

def _parse_shell_reads(cmd, cwd=None):
    """Extract file paths read via shell commands in a Bash tool call.

    Returns list of absolute-or-relative paths, excluding system paths and
    entries that look like flags, glob patterns, or shell variables.
    """
    found = []
    seen = set()
    for pattern in _SHELL_READ_PATTERNS:
        for m in re.finditer(pattern, cmd):
            raw = m.group(1).strip(" \"'")
            if not raw or raw.startswith('-') or raw.startswith('$'):
                continue
            if '*' in raw or '?' in raw:
                continue
            # Must contain a dot or slash to look like a real file path
            if '.' not in raw and '/' not in raw:
                continue
            # Resolve relative paths against cwd
            if cwd and not os.path.isabs(raw):
                resolved = str(Path(cwd) / raw)
            else:
                resolved = raw
            # Skip system paths
            if any(resolved.startswith(p) for p in _SHELL_READ_SYSTEM_PREFIXES):
                continue
            if resolved not in seen:
                seen.add(resolved)
                found.append(resolved)
    return found

def _extract_apply_patch_artifacts(patch_text):
    """Parse apply_patch payload into (path, action) pairs.

    Collapses A+D on the same path into 'modified' so that a Delete+Add sequence
    for the same file doesn't produce a conflicting (created, deleted) pair.
    """
    if not patch_text:
        return []
    # Collect ordered ops per path (preserving first occurrence order for output)
    ops_by_path = {}  # path → set of op chars
    path_order = []   # insertion order
    for line in patch_text.splitlines():
        if line.startswith("*** Add File: "):
            path = line[len("*** Add File: "):].strip()
            op = "A"
        elif line.startswith("*** Update File: "):
            path = line[len("*** Update File: "):].strip()
            op = "U"
        elif line.startswith("*** Delete File: "):
            path = line[len("*** Delete File: "):].strip()
            op = "D"
        elif line.startswith("*** Move to: "):
            path = line[len("*** Move to: "):].strip()
            op = "M"
        else:
            continue
        if path not in ops_by_path:
            ops_by_path[path] = set()
            path_order.append(path)
        ops_by_path[path].add(op)

    result = []
    for path in path_order:
        ops = ops_by_path[path]
        if "A" in ops and "D" in ops:
            # Delete + Add on same path → file was rewritten → modified
            result.append((path, "modified"))
        elif "A" in ops:
            result.append((path, "created"))
        elif "D" in ops:
            result.append((path, "deleted"))
        elif "U" in ops:
            result.append((path, "modified"))
        elif "M" in ops:
            result.append((path, "moved"))
    return result

def _make_artifact(file_path, action):
    ext = Path(file_path).suffix.lower()
    return {"file_path": file_path, "action": action, "is_code": int(ext in CODE_EXT), "is_doc": int(ext in DOC_EXT)}


def _is_path_outside_cwd(file_path, cwd_resolved):
    """Return True if file_path is an absolute/home path that resolves outside cwd_resolved."""
    if not file_path or not cwd_resolved:
        return False
    if file_path.startswith("event:"):
        return False
    try:
        if os.path.isabs(file_path) or file_path.startswith("~"):
            abs_path = str(Path(file_path).expanduser().resolve())
            return not abs_path.startswith(cwd_resolved)
    except Exception:
        pass
    return False


def extract_artifacts(tool_calls, cwd=None, tool_errors=None):
    artifacts = []
    # seen_write tracks files already recorded as write-type actions (created/modified/deleted).
    # Read calls are intentionally excluded so a prior Read never blocks a subsequent Edit/Write
    # from being captured as a diff artifact.
    seen_write = set()
    seen_read  = set()
    initial_creates = set()  # files created via Write in this session (for ephemeral detection)
    cwd_resolved = str(Path(cwd).expanduser().resolve()) if cwd else None
    tool_errors = tool_errors or {}
    for tc in tool_calls:
        # Skip tool calls that returned is_error=True — they had no effect on the filesystem
        tc_id = tc.get("id")
        if tc_id and tool_errors.get(tc_id):
            continue
        tool = tc["tool"]
        inp  = tc.get("input", {})
        path = action = None

        if tool == "Write":
            path = inp.get("file_path")
            if _is_path_outside_cwd(path, cwd_resolved):
                continue
            # If the file was read earlier in this session, it already existed → modified.
            action = "modified" if path and path in seen_read else "created"
            # Also check git tracking: if file is tracked, it existed before → modified.
            if path and action == "created" and cwd_resolved:
                try:
                    r = subprocess.run(
                        ["git", "ls-files", "--error-unmatch", path],
                        capture_output=True, cwd=cwd_resolved, check=False, timeout=3,
                    )
                    if r.returncode == 0:
                        action = "modified"
                except Exception:
                    pass
            if path and action == "created":
                initial_creates.add(path)
        elif tool == "Edit":
            path = inp.get("file_path")
            if _is_path_outside_cwd(path, cwd_resolved):
                continue
            action = "modified"
        elif tool == "Read":
            path = inp.get("file_path")
            if _is_path_outside_cwd(path, cwd_resolved):
                continue
            action = "read"
        elif tool in ("Bash", "exec_command"):
            cmd = inp.get("command") or inp.get("cmd") or inp.get("raw", "")
            artifacts.extend(_detect_command_events(cmd))
            # Parse shell-read commands (cat, sed, head, tail, rg, git diff…) → action=read (SA-T033)
            for shell_path in _parse_shell_reads(cmd, cwd=cwd):
                if shell_path not in seen_write and shell_path not in seen_read:
                    seen_read.add(shell_path)
                    ext = Path(shell_path).suffix.lower()
                    artifacts.append({
                        "file_path": shell_path,
                        "action":    "read",
                        "is_code":   int(ext in CODE_EXT),
                        "is_doc":    int(ext in DOC_EXT),
                    })
            # Parse mv src dst
            for src, dst in re.findall(r'\bmv\s+(\S+)\s+(\S+)', cmd):
                src = src.strip("\"'")
                dst = dst.strip("\"'")
                # Skip shell variables ($var), glob patterns, and bare names without path chars
                if src.startswith('$') or dst.startswith('$'):
                    continue
                if '*' in src or '?' in src:
                    continue
                if '/' not in src and '.' not in src:
                    continue
                if src and not src.startswith('-') and dst and not dst.startswith('-'):
                    if src in seen_write:
                        for i, a in enumerate(artifacts):
                            if a.get("file_path") == src:
                                artifacts[i] = _make_artifact(src, "moved_from")
                                break
                    else:
                        seen_write.add(src)
                        artifacts.append(_make_artifact(src, "moved_from"))
                    if dst not in seen_write:
                        seen_write.add(dst)
                        artifacts.append(_make_artifact(dst, "moved_to"))
            # Parse rm [-flags] path
            for path_rm in re.findall(r'\brm\s+(?:-[a-zA-Z]+\s+)*(\S+)', cmd):
                path_rm = path_rm.strip("\"'")
                if path_rm and not path_rm.startswith('-'):
                    # SA-T031: resolve relative paths against cwd to match abs-path Write entries
                    path_rm_abs = (str(Path(cwd_resolved) / path_rm)
                                   if cwd_resolved and not os.path.isabs(path_rm) else path_rm)
                    canonical = (path_rm if path_rm in seen_write
                                 else path_rm_abs if path_rm_abs in seen_write else None)
                    if canonical is not None:
                        for i, a in enumerate(artifacts):
                            if a.get("file_path") == canonical:
                                artifacts[i] = _make_artifact(canonical, "deleted")
                                break
                    else:
                        key = path_rm_abs if os.path.isabs(path_rm_abs) else path_rm
                        seen_write.add(key)
                        artifacts.append(_make_artifact(key, "deleted"))
        elif tool == "apply_patch":
            patch_text = inp.get("raw", "")
            for patch_path, patch_action in _extract_apply_patch_artifacts(patch_text):
                if patch_path and patch_path not in seen_write:
                    seen_write.add(patch_path)
                    ext = Path(patch_path).suffix.lower()
                    artifacts.append({
                        "file_path": patch_path,
                        "action": patch_action,
                        "is_code": int(ext in CODE_EXT),
                        "is_doc": int(ext in DOC_EXT),
                    })

        if not path:
            continue

        if action == "read":
            # Record Read only if the file was never written in this session
            if path not in seen_write and path not in seen_read:
                seen_read.add(path)
                ext = Path(path).suffix.lower()
                artifacts.append({
                    "file_path": path,
                    "action":    action,
                    "is_code":   int(ext in CODE_EXT),
                    "is_doc":    int(ext in DOC_EXT),
                })
        else:
            # Write-type action: always record, upgrade Read→write if already present
            if path not in seen_write:
                seen_write.add(path)
                ext = Path(path).suffix.lower()
                if path in seen_read:
                    # Replace the earlier read-only entry with the write action
                    for i, a in enumerate(artifacts):
                        if a["file_path"] == path and a["action"] == "read":
                            artifacts[i] = {
                                "file_path": path,
                                "action":    action,
                                "is_code":   int(ext in CODE_EXT),
                                "is_doc":    int(ext in DOC_EXT),
                            }
                            break
                else:
                    artifacts.append({
                        "file_path": path,
                        "action":    action,
                        "is_code":   int(ext in CODE_EXT),
                        "is_doc":    int(ext in DOC_EXT),
                    })

    # Post-check: if file no longer exists on disk, mark as deleted
    EVENT_ACTIONS = {"event:commit", "event:push", "event:pr_created", "event:deploy", "event:tests"}
    if cwd:
        for i, art in enumerate(artifacts):
            if art.get("action") in EVENT_ACTIONS:
                continue
            fp = art["file_path"]
            if art["action"] in ("modified", "created"):
                full_path = fp if os.path.isabs(fp) else os.path.join(cwd, fp)
                if not os.path.exists(full_path):
                    artifacts[i] = _make_artifact(fp, "deleted")

    # Remove ephemeral artifacts: created via Write then deleted in same session
    artifacts = [
        a for a in artifacts
        if not (a.get("action") == "deleted" and a.get("file_path") in initial_creates)
    ]

    return artifacts

_TASK_ID_RE = re.compile(r"(?<![A-Za-z])([A-Z]{0,5}-?T\d{2,4})(?!\d)", re.IGNORECASE)

def extract_task_ids(tool_calls, messages=None):
    """Extract task IDs from evidence of actual work: Edit/Write to task files, Bash mv, and user messages.

    Scans:
    1. Edit/Write/MultiEdit tool calls for task file paths (e.g. SA-T288_...md).
    2. Bash mv/cp commands for task file paths (e.g. mv SA-T015.md Done/).
    3. User messages for explicit T-number mentions (role=='user' text only).

    Does NOT scan tool_result, assistant messages, or summary_override text to avoid
    false positives from HANDOFF/system-reminder/skill-template context.
    Does NOT scan skill-prompt messages (containing <command-message>) to avoid
    false positives from skill examples.
    """
    task_ids = set()
    for tc in (tool_calls or []):
        if tc.get("tool") in ("Edit", "Write", "MultiEdit"):
            fp = (tc.get("input") or {}).get("file_path") or ""
            for m in _TASK_ID_RE.finditer(fp):
                task_ids.add(m.group(1).upper())
        elif tc.get("tool") in ("Bash", "exec_command"):
            cmd = (tc.get("input") or {}).get("command") or (tc.get("input") or {}).get("cmd") or ""
            # Only scan mv/cp/rename commands — these evidence actual task file moves
            if re.match(r'\s*(?:mv|cp|rename)\s', cmd):
                for m in _TASK_ID_RE.finditer(cmd):
                    task_ids.add(m.group(1).upper())
    # User messages: explicit T-number mentions typed by the user.
    # Strip injected context (ide_opened_file, system-reminder etc.) and
    # skip skill-prompt messages (contain <command-message>) to avoid examples inside skills.
    for msg in (messages or []):
        if msg.get("role") != "user":
            continue
        text = msg.get("text", "")
        # Skip skill invocation messages — their content is skill template, not user intent
        if "<command-message>" in text or "<command-name>" in text:
            continue
        text = _INJECTED_CONTEXT_RE.sub("", text)
        for m in _TASK_ID_RE.finditer(text):
            task_ids.add(m.group(1).upper())
    return sorted(task_ids)

def detect_events(messages, artifacts):
    seen   = set()
    events = []

    def add(event_type):
        if event_type not in seen:
            seen.add(event_type)
            events.append({"event_type": event_type, "detail": None})

    # Read-based events: только если файл реально читался через Read tool
    read_paths = {a["file_path"].lower() for a in artifacts if a.get("action") == "read" and a.get("file_path")}
    for path in read_paths:
        if "handoff" in path:
            add("handoff_read")
        if "changelog" in path:
            add("changelog_read")
        if re.search(r'adv-s\d+|spec', path):
            add("spec_read")

    # Command-based events: из artifact action labels
    label_map = {
        "event:commit":     "commit_made",
        "event:push":       "push_made",
        "event:deploy":     "deploy",
        "event:tests":      "tests_run",
        "event:pr_created": "pr_created",
    }
    for a in artifacts:
        if a.get("action") in label_map:
            add(label_map[a["action"]])

    # session_archived добавляется всегда — archive-current вызывается только для завершённых сессий
    add("session_archived")

    return events

def detect_domains(artifacts):
    """Определить domains только по file_path изменённых/созданных/удалённых артефактов."""
    DOMAIN_RULES = {
        "frontend": [r'\.(tsx?|jsx?|css|scss|html|vue|svelte)$', r'/(components|pages|ui|views|styles)/'],
        "backend":  [r'\.(py|go|rs|rb|java|php)$', r'/(api|handlers|routes|services)/'],
        "database": [r'\.(sql|migration)$', r'/(migrations|models|schemas)/'],
        "docs":     [r'\.(md|rst|txt)$', r'/(docs|documentation)/'],
        "tests":    [r'(test_|_test\.|spec\.|\.test\.)', r'/(tests?|spec)/'],
        "ci_cd":    [r'\.(yml|yaml)$', r'/(\.github|\.gitlab|ci|deploy)/'],
    }
    domains = set()
    for artifact in artifacts:
        if artifact.get("action") not in ("modified", "created", "deleted"):
            continue
        path = artifact.get("file_path", "")
        for domain, patterns in DOMAIN_RULES.items():
            if any(re.search(p, path) for p in patterns):
                domains.add(domain)
    return sorted(domains)

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

_SKILL_BLOCKLIST = {
    # XML-теги, которые попадают в текст как имена тегов
    "command-message", "command-name", "command-args",
    "task-id", "task-notification", "tool-use-id",
    "output-file", "private", "status", "summary",
    # Компоненты путей и опций из system-reminder
    "users", "home", "opt", "etc", "tmp", "path", "projects",
    "personal", "hooks", "memory", "json", "localhost",
    # Системные слова, не являющиеся скиллами
    "dev", "ide", "subagents", "rename", "restart", "some-dir",
    "is", "claude", "codex", "verify", "archive", "session",
}

def _find_archive_boundary_idx(tool_calls):
    """Return index of first archive-session Skill call or archive-current Bash call.

    Skill calls at index >= boundary are excluded from skill tags (post-archive plans).
    Returns len(tool_calls) if no archive boundary found (= process all calls).
    """
    for i, tc in enumerate(tool_calls):
        tool = tc.get("tool", "")
        inp = tc.get("input") or {}
        if tool == "Skill":
            skill = (inp.get("skill") or "").lower()
            if "archive" in skill:
                return i
        if tool in ("Bash", "exec_command"):
            cmd = inp.get("command") or inp.get("cmd") or ""
            if "archive-current" in cmd and "session_archive" in cmd:
                return i
    return len(tool_calls)


# ── Evidence Accumulator (SA-T029) ───────────────────────────────────────────

class EvidenceAccumulator:
    """Structured facts from JSONL tool calls — single source of truth for derivers.

    Separates evidence accumulation (what happened) from derivation (what it means).
    Replaces text-heuristic extraction with tool-call-verified evidence.

    Attributes:
        write_paths:      set of file paths actually written (Write/Edit/MultiEdit tool calls)
        read_paths:       set of file paths actually read via Read tool (full reads only)
        bash_calls:       list of (cmd: str, is_error: bool) for each Bash/exec_command call
        skill_names:      skill names from Skill tool calls before archive_boundary
        task_file_edits:  task IDs extracted from Edit/Write tool call file paths
        archive_boundary: index of first archive-session call in tool_calls
        cwd:              working directory
    """

    def __init__(self):
        self.write_paths = set()
        self.read_paths = set()
        self.bash_calls = []        # list of (cmd, is_error)
        self.skill_names = []
        self.task_file_edits = []
        self.archive_boundary = 0
        self.cwd = None


def build_evidence(parsed_data):
    """Populate EvidenceAccumulator from parsed JSONL result dict.

    Collects tool-call-verified evidence from the session:
    - Write/Edit paths (actual file modifications)
    - Read paths (files explicitly read with Read tool)
    - Bash calls with exit-code status (is_error=False → success)
    - Skill invocations before archive boundary
    - Task IDs from task-file edit paths
    """
    ev = EvidenceAccumulator()
    ev.cwd = parsed_data.get("cwd")

    tool_calls = parsed_data.get("tool_calls", [])
    tool_errors = parsed_data.get("tool_errors", {})
    ev.archive_boundary = _find_archive_boundary_idx(tool_calls)

    for i, tc in enumerate(tool_calls):
        tc_id = tc.get("id")
        is_err = bool(tc_id and tool_errors.get(tc_id))
        tool = tc.get("tool", "")
        inp = tc.get("input") or {}

        if tool in ("Write", "Edit", "MultiEdit"):
            fp = inp.get("file_path", "")
            if fp:
                ev.write_paths.add(fp)
                for m in _TASK_ID_RE.finditer(fp):
                    ev.task_file_edits.append(m.group(1).upper())

        elif tool == "Read":
            fp = inp.get("file_path", "")
            # Only full reads (no offset/limit) are reliable baseline evidence
            if fp and not inp.get("offset") and not inp.get("limit"):
                ev.read_paths.add(fp)

        elif tool in ("Bash", "exec_command"):
            cmd = inp.get("command") or inp.get("cmd") or ""
            if cmd:
                ev.bash_calls.append((cmd, is_err))

        elif tool == "Skill" and i < ev.archive_boundary:
            skill_name = inp.get("skill", "").strip().lower()
            if skill_name:
                ev.skill_names.append(skill_name)

    return ev


def derive_domain_tags(evidence):
    """Derive domain tags from evidence: file extensions of written paths only.

    Evidence-based replacement for detect_domains(artifacts).
    Uses evidence.write_paths (actual tool-call modifications) for classification.

    Key difference from detect_domains():
      - NO directory-based heuristics for database (models/ ≠ database)
      - Extension-only matching prevents BUG-TAGS-DOMAIN-DATABASE-FALSE
      - YAML files only counted for ci_cd when in CI/CD directories
    """
    domains = set()
    paths = list(evidence.write_paths)

    for p in paths:
        pl = p.lower()
        if re.search(r'\.(tsx?|jsx?|css|scss|html|vue|svelte)$', pl):
            domains.add('frontend')
        if re.search(r'\.(py|go|rs|rb|java|php|cs)$', pl):
            domains.add('backend')
        # database: .sql files or 'migration' in path ONLY (not models/ — BUG-TAGS-DOMAIN-DATABASE-FALSE)
        if pl.endswith('.sql') or 'migration' in pl:
            domains.add('database')
        if re.search(r'\.(md|rst)$', pl):
            domains.add('docs')
        if re.search(r'(test_|_test\.|spec\.|\.test\.|/tests?/|/spec/)', pl):
            domains.add('tests')
        if re.search(r'\.(yml|yaml)$', pl) and re.search(r'/(\.github|\.gitlab|ci|deploy)/', pl):
            domains.add('ci_cd')

    return sorted(domains)


def detect_skills_used(messages, tool_calls, agent_family):
    found = set()

    # Archive boundary: exclude Skill calls after archive-session invocation
    # (they represent planned but not-yet-executed skills in the same conversation).
    archive_boundary = _find_archive_boundary_idx(tool_calls)

    if agent_family == "claude":
        for m in messages:
            if m["role"] != "user":
                continue
            text = m["text"]
            # 1. /skillname lines typed directly
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("/"):
                    match = re.match(r'^/([a-z][a-z0-9-]{1,29})(?:\s|$)', line)
                    if match:
                        found.add(match.group(1))
            # 2. <command-name>/skillname</command-name> tag (first 500 chars = header area)
            head = text[:500]
            for match in re.finditer(r'<command-name>/?([^<\s]{1,30})</command-name>', head):
                name = match.group(1).lstrip("/").lower()
                if re.match(r'^[a-z][a-z0-9-]{1,29}$', name):
                    found.add(name)
            # 3. <command-message>skillname</command-message> (fallback for older formats)
            for match in re.finditer(r'<command-message>([^<\s]{1,30})</command-message>', head):
                name = match.group(1).strip().lower()
                if re.match(r'^[a-z][a-z0-9-]{1,29}$', name):
                    found.add(name)

    for i, tc in enumerate(tool_calls):
        # Primary: detect actual Skill tool invocations (before archive boundary)
        if tc.get("tool") == "Skill" and i < archive_boundary:
            skill_name = (tc.get("input") or {}).get("skill", "").strip().lower()
            if skill_name:
                found.add(skill_name)
        # Secondary: detect Codex skill/command file references (no boundary needed — these
        # are always historical references to executed skills, not future plans)
        blob = json.dumps(tc.get("input", {}), ensure_ascii=False)
        found.update(re.findall(r'/\.codex/skills/([^/\s]+)/SKILL\.md', blob))
        found.update(re.findall(r'/\.claude/commands/([a-z0-9-]+)\.md', blob))

    return sorted(s for s in found if s not in _SKILL_BLOCKLIST)

# Patterns that indicate stdout from scripts or reasoning/meta text — NOT real open issues.
_OPEN_ISSUES_NOISE_RE = re.compile(
    r'Удалено\s+\d+|осталось:\s*\d+'          # Python script stdout ("Удалено 19 сессий, осталось: 55")
    r'|^\d+\.\s+\S'                            # Numbered reasoning list ("3. Events: tests_run — ложный")
    r'|archive.session\s+не\s+запускал'        # verify-archive meta ("archive-session не запускался")
    r'|Теперь\s+фикш'                          # reasoning ("Теперь фикшу export MD...")
    r'|Противоречие\s+было'                    # reasoning
    r'|Контекст\s+уже\s+есть',
    re.IGNORECASE,
)

_STRIP_MARKDOWN_RE = re.compile(r'\*{1,2}([^*\n]+)\*{1,2}|_{1,2}([^_\n]+)_{1,2}|`([^`\n]+)`|^#{1,6}\s+', re.MULTILINE)

def _strip_markdown(text: str) -> str:
    """Remove markdown formatting (*bold*, _italic_, `code`, ## heading) for plain-text storage."""
    def _replace(m):
        return m.group(1) or m.group(2) or m.group(3) or ""
    return _STRIP_MARKDOWN_RE.sub(_replace, text).strip()

def extract_open_issues(messages):
    patterns = [
        "open issue", "open issues", "follow-up", "follow up", "blocker",
        "not run", "did not run", "remaining", "left unfinished",
        "не запускал", "не запускались", "не выполнен", "не выполнено",
        "блокер", "followup",
        # Note: "осталось" removed — too broad, matches Python stdout ("осталось: 55 сессий")
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
            # Filter noise: stdout patterns, reasoning text, numbered meta-lists
            if _OPEN_ISSUES_NOISE_RE.search(raw_line.strip()):
                continue
            if any(pattern in low for pattern in patterns):
                clean = _truncate(_strip_markdown(line), 240)
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
    # Use splitlines() without keepends so each line has no trailing \n.
    # Combined with lineterm="", "\n".join(diff_lines) produces clean single-newline output.
    before_lines = (before_text or "").splitlines()
    after_lines = (after_text or "").splitlines()
    clean_path = file_path.lstrip("/")
    diff_lines = unified_diff(
        before_lines,
        after_lines,
        fromfile=f"a/{clean_path}",
        tofile=f"b/{clean_path}",
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

def _collect_tool_diff_hints(tool_calls, project_root, tool_errors=None):
    hints = {}
    tool_errors = tool_errors or {}

    def remember(path_key, diff_text, source):
        if not path_key or not diff_text:
            return
        if path_key in hints:
            # Accumulate multiple snippets for the same file (e.g. multiple Edit calls),
            # but skip identical snippets to avoid duplicate diff blocks.
            existing = hints[path_key]["diff"] or ""
            if diff_text.strip() and diff_text.strip() not in existing:
                hints[path_key]["diff"] = _truncate_diff_text(existing + "\n\n" + diff_text)
        else:
            hints[path_key] = {
                "diff": _truncate_diff_text(diff_text),
                "diff_source": source,
            }

    for tc in tool_calls:
        # Skip failed tool calls — they produced no filesystem change
        tc_id = tc.get("id")
        if tc_id and tool_errors.get(tc_id):
            continue
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
        # SA-T035/SA-T031: use base_commit..HEAD (committed range only) to avoid capturing
        # pre-session uncommitted working-tree changes and to aggregate all commits in session.
        diff_text = _run_git(
            project_root,
            ["diff", "--no-ext-diff", "--find-renames", "--binary", "--relative",
             f"{base_commit}..HEAD", "--", rel_path],
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

def _synthetic_diff_for_artifact(project_root, rel_path, path_obj, action, read_snapshots=None):
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
        # For untracked files: use Read snapshot from this session as baseline if available
        if read_snapshots:
            snapshot = read_snapshots.get(path_obj and str(path_obj)) or read_snapshots.get(rel_path)
            if snapshot is None and project_root:
                abs_path = str(Path(project_root) / rel_path)
                snapshot = read_snapshots.get(abs_path)
            # Discard snapshot if it is a Read-tool error string (file was too large to read)
            if snapshot is not None and "exceeds maximum" in snapshot:
                snapshot = None
            if snapshot is not None:
                before_text = snapshot

    if before_text is None:
        # SA-T035: for modified files with no baseline, don't show full content as @@ -0,0 +1,N @@.
        # Return None so edit_snippet hints (old_string/new_string) can be used as fallback.
        if action == "modified":
            return None
        # For created files: skip large files to avoid huge @@ -0,0 +1,N @@
        if path_obj and path_obj.exists():
            try:
                file_bytes = path_obj.stat().st_size
                if file_bytes > SYNTHETIC_DIFF_MAX_BYTES:
                    return None  # diff_source='manual' upstream
                line_count = (current_text or "").count("\n") + 1
                if line_count > SYNTHETIC_DIFF_MAX_LINES:
                    return None  # diff_source='manual' upstream
            except OSError:
                pass
        return _truncate_diff_text(_build_unified_diff(rel_path, "", current_text or ""))

    if before_text == current_text:
        return None
    return _truncate_diff_text(_build_unified_diff(rel_path, before_text, current_text or ""))

def _resolve_artifact_diff(item, project_root, base_commit, tool_diff_hints, read_snapshots=None):
    rel_path = _normalize_artifact_key(project_root, item.get("file_path"))
    if not rel_path or rel_path.startswith("event:"):
        return None, None

    diff_text, diff_source = _git_diff_for_artifact(project_root, base_commit, rel_path)
    if diff_text:
        return diff_text, diff_source

    # Synthetic diff (current file vs git HEAD, or full content for untracked files) is preferred
    # over edit_snippet hints: for untracked files it gives the complete picture, and for tracked
    # files it correctly reflects uncommitted state. Snippet hints are a last resort when the file
    # no longer exists on disk or synthetic produces nothing.
    path_obj = _resolve_artifact_path(project_root, item.get("file_path"))
    diff_text = _synthetic_diff_for_artifact(
        project_root, rel_path, path_obj, item.get("action"), read_snapshots=read_snapshots
    )
    if diff_text:
        return diff_text, "synthetic"

    hint = tool_diff_hints.get(rel_path)
    if hint:
        return hint.get("diff"), hint.get("diff_source")

    return None, None

def _enrich_from_git_status(artifacts, project_root):
    """Add to artifacts any git-tracked files changed that aren't captured by tool calls.
    Catches files modified via bash commands, go mod, IDE, /accept, etc. (SA-T018)."""
    if not project_root:
        return artifacts
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=project_root, timeout=5, check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return artifacts
    except Exception:
        return artifacts

    # Build set of already-known paths (normalized relative to project_root)
    known_paths = set()
    for art in artifacts:
        fp = art.get("file_path") or ""
        if not fp or fp.startswith("event:"):
            continue
        rel = _normalize_artifact_key(project_root, fp)
        if rel:
            known_paths.add(rel)

    new_artifacts = list(artifacts)
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        x, y = xy[0], xy[1]
        # Skip untracked (??) and ignored (!!) — only want tracked file changes
        if x == '?' or x == '!':
            continue
        rest = line[3:]
        # Renames: "R  old -> new"
        if ' -> ' in rest:
            old_path, new_path = rest.split(' -> ', 1)
            old_path = old_path.strip().strip('"')
            new_path = new_path.strip().strip('"')
            for fp, act in [(old_path, "moved_from"), (new_path, "moved_to")]:
                rel = _normalize_artifact_key(project_root, fp)
                if rel and rel not in known_paths:
                    known_paths.add(rel)
                    ext = Path(fp).suffix.lower()
                    new_artifacts.append({
                        "file_path": fp,
                        "action": act,
                        "is_code": int(ext in CODE_EXT),
                        "is_doc": int(ext in DOC_EXT),
                    })
            continue
        file_path = rest.strip().strip('"')
        rel = _normalize_artifact_key(project_root, file_path)
        if not rel or rel in known_paths:
            continue
        if x == 'D' or y == 'D':
            action = "deleted"
        elif x == 'A':
            action = "created"
        else:
            action = "modified"
        known_paths.add(rel)
        ext = Path(file_path).suffix.lower()
        new_artifacts.append({
            "file_path": file_path,
            "action": action,
            "is_code": int(ext in CODE_EXT),
            "is_doc": int(ext in DOC_EXT),
        })
    return new_artifacts


def enrich_artifacts(artifacts, project_path, tool_calls=None, base_commit=None, read_snapshots=None, tool_errors=None):
    project_root = detect_git_root(project_path) or project_path
    project_root = str(Path(project_root).resolve()) if project_root else None
    tool_diff_hints = _collect_tool_diff_hints(tool_calls or [], project_root, tool_errors=tool_errors or {})
    read_snapshots = read_snapshots or {}
    # SA-T018: add files modified via bash/external tools not captured by tool call parsing
    artifacts = _enrich_from_git_status(artifacts, project_root)
    enriched = []
    for artifact in artifacts:
        item = dict(artifact)
        file_path = item.get("file_path") or ""
        action = item.get("action")
        if action in ("created", "modified") and file_path and not file_path.startswith("event:"):
            content = _read_text_file(_resolve_artifact_path(project_root, file_path))
            item["content"] = content[:MAX_ARTIFACT_CONTENT] if content is not None else None
        if action in DIFF_ACTIONS and file_path and not file_path.startswith("event:"):
            diff_text, diff_source = _resolve_artifact_diff(
                item, project_root, base_commit, tool_diff_hints, read_snapshots=read_snapshots
            )
            item["diff"] = diff_text
            item["diff_source"] = diff_source
        enriched.append(item)
    return enriched

_ARTIFACT_ACTION_PRIORITY = {
    "read": 0,
    "modified": 30,
    "moved": 40,
    "moved_from": 40,
    "moved_to": 40,
    "created": 50,
    "deleted": 60,
}

def _artifact_action_priority(action):
    return _ARTIFACT_ACTION_PRIORITY.get(action or "", 10)

def _merge_artifact_records(existing, incoming):
    merged = dict(existing)

    if _artifact_action_priority(incoming.get("action")) >= _artifact_action_priority(existing.get("action")):
        merged["action"] = incoming.get("action")

    merged["is_code"] = int(bool(existing.get("is_code")) or bool(incoming.get("is_code")))
    merged["is_doc"] = int(bool(existing.get("is_doc")) or bool(incoming.get("is_doc")))

    for key in ("content", "diff", "diff_source"):
        if incoming.get(key) and (not merged.get(key) or len(str(incoming.get(key))) > len(str(merged.get(key)))):
            merged[key] = incoming.get(key)

    return merged

def collapse_artifacts_by_path(artifacts):
    if not artifacts:
        return []

    collapsed = {}
    order = []
    for artifact in artifacts:
        path = artifact.get("file_path")
        if not path:
            continue
        if path not in collapsed:
            collapsed[path] = dict(artifact)
            order.append(path)
            continue
        collapsed[path] = _merge_artifact_records(collapsed[path], artifact)

    return [collapsed[path] for path in order]

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

_SUMMARY_META_WORDS = re.compile(
    r'\b(verify-archive|archive-session|archive-current|session-archive)\b',
    re.IGNORECASE,
)

def build_summary(messages, task_ids, spec_ids, open_issues):
    assistant_messages = [m for m in messages if m.get("role") == "assistant" and m.get("text")]
    parts = []

    goal = _truncate(_select_goal(messages), 220)
    # Strip archive/verify management phrases from goal (they appear when /intro loads HANDOFF
    # or when user invokes /archive-session as part of the conversation).
    if goal:
        goal = _SUMMARY_META_WORDS.sub("", goal).strip(" .,;")
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
    tool_errors = data.get("tool_errors", {})
    all_tool_calls = data["tool_calls"]
    # Apply archive boundary: only extract artifacts from tool calls before the
    # archive-session invocation to avoid phantom context from previous sessions
    # archived in the same conversation (SA-T017).
    archive_boundary = _find_archive_boundary_idx(all_tool_calls)
    artifact_tool_calls = all_tool_calls[:archive_boundary]
    artifacts = extract_artifacts(artifact_tool_calls, cwd=data.get("cwd"), tool_errors=tool_errors)
    task_ids = extract_task_ids(all_tool_calls, data["messages"])
    events = detect_events(data["messages"], artifacts)

    # SA-T029: Evidence-based domain tag derivation.
    # Build EvidenceAccumulator from pre-boundary tool calls only,
    # then derive domain tags from extension-only rules (no directory heuristics).
    # This fixes BUG-TAGS-DOMAIN-DATABASE-FALSE: models/ directory no longer implies database.
    evidence = build_evidence({**data, "tool_calls": artifact_tool_calls})
    domains = derive_domain_tags(evidence)

    return {
        **{k: v for k, v in data.items() if k not in ("tool_calls",)},
        "agent_family": data.get("agent_family"),
        "ai_model": data.get("model"),
        "msg_count": len(data["messages"]),
        "tool_call_count": len(all_tool_calls),
        "user_msg_count": sum(1 for m in data["messages"] if m["role"] == "user"),
        "task_ids": task_ids,
        "events": events,
        "domains": domains,
        "artifacts": artifacts,
        "tool_errors": tool_errors,
    }

def build_metadata(parsed, summary_override=None, model_override=None, cwd_override=None):
    project_path = cwd_override or parsed.get("cwd") or os.getcwd()
    project_path = str(Path(project_path).expanduser().resolve())
    agent_family = infer_agent_family(parsed)
    task_ids = list(parsed.get("task_ids") or [])
    # NOTE: T-numbers from summary_override are intentionally NOT merged here.
    # summary_override text can contain task IDs from HANDOFF/skill context (drift).
    # Task IDs are determined only from Edit/Write tool call file paths and user messages.
    spec_ids = extract_spec_ids(parsed.get("messages", []))
    open_issues = extract_open_issues(parsed.get("messages", []))
    repo_name = detect_repo_name(project_path)
    branch = parsed.get("branch") or detect_git_branch(project_path)
    ai_model = model_override or parsed.get("ai_model") or ("claude" if agent_family == "claude" else "codex")
    skills_used = detect_skills_used(parsed.get("messages", []), parsed.get("tool_calls", []), agent_family)
    tasks_text = " ".join(m["text"] for m in parsed.get("messages", [])).lower()

    tags = [
        {"category": "assistant", "value": ai_model},
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
    # Spec IDs (SA-S01, ADV-S03 etc.) are NOT added to session_tasks per BUG-TASKS-FALSE-POSITIVE fix.
    # They are kept in spec_ids for use in summary/build_summary only.

    # Filter messages to before the archive-session boundary to avoid summary drift
    # from verify-archive tails or post-archive mcp-fix messages (SA-T026).
    all_messages = parsed.get("messages", [])
    tool_calls = parsed.get("tool_calls", [])
    archive_boundary_idx = _find_archive_boundary_idx(tool_calls)
    if archive_boundary_idx < len(tool_calls):
        boundary_ts = tool_calls[archive_boundary_idx].get("timestamp") or ""
        if boundary_ts:
            pre_archive_messages = [m for m in all_messages
                                    if (m.get("timestamp") or "") < boundary_ts]
            summary_messages = pre_archive_messages if pre_archive_messages else all_messages
        else:
            summary_messages = all_messages
    else:
        summary_messages = all_messages

    auto_summary = build_summary(summary_messages, task_ids, spec_ids, open_issues)
    summary = summary_override or auto_summary

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
        "summary_manual": summary_override if summary_override else None,
        "msg_count": parsed.get("msg_count", 0),
        "user_msg_count": parsed.get("user_msg_count", 0),
        "tool_call_count": parsed.get("tool_call_count", 0),
        "raw_jsonl_path": parsed.get("jsonl_path"),
        "tags": tags,
        "tasks": tasks,
        "artifacts": collapse_artifacts_by_path(
            enrich_artifacts(
                parsed.get("artifacts", []),
                project_path,
                tool_calls=parsed.get("tool_calls", []),
                base_commit=parsed.get("base_commit"),
                read_snapshots=parsed.get("read_snapshots", {}),
                tool_errors=parsed.get("tool_errors", {}),
            )
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
                if "subagents" not in path.parts:
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
        stat = path.stat()
        score = (
            stat.st_mtime_ns,
            stat.st_size,
            info.get("last_ts") or "",
            info.get("first_ts") or "",
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

def write_session(metadata: dict, force: bool = False) -> tuple:
    conn = get_db()
    sid = metadata["session_id"]
    agent_family = infer_agent_family(metadata)

    open_issues = metadata.get("open_issues")
    if isinstance(open_issues, list):
        open_issues = json.dumps(open_issues, ensure_ascii=False)

    tags = list(metadata.get("tags", []))
    if not any(tag.get("category") == "assistant" for tag in tags):
        tags.append({"category": "assistant", "value": agent_family})

    # Preserve manually-set summary: if session already exists with summary_manual, keep it.
    existing = conn.execute(
        "SELECT summary_manual, manually_reviewed FROM sessions WHERE id=?", (sid,)
    ).fetchone()
    summary_manual = metadata.get("summary_manual")
    if existing and existing["summary_manual"] and not summary_manual:
        # Keep existing manual summary; use it as the effective summary too
        summary_manual = existing["summary_manual"]
        effective_summary = summary_manual
    else:
        effective_summary = summary_manual or metadata.get("summary", "")

    # Protect manually-reviewed sessions from accidental re-extraction.
    # If a session was manually corrected, skip re-inserting tags/tasks/events/messages
    # unless --force is passed. Only update counts and model.
    is_manually_reviewed = bool(existing and existing["manually_reviewed"])
    if is_manually_reviewed and not force:
        print(
            f"Warning: session {sid[:8]} is manually reviewed. "
            "Updating counts only. Use --force to re-extract all fields.",
            file=sys.stderr,
        )
        # If --summary was explicitly provided, always update it even in manually_reviewed mode
        new_summary_manual = metadata.get("summary_manual")
        if new_summary_manual:
            conn.execute(
                "UPDATE sessions SET msg_count=?, tool_call_count=?, ai_model=?,"
                " summary=?, summary_manual=? WHERE id=?",
                (metadata.get("msg_count", 0), metadata.get("tool_call_count", 0),
                 metadata.get("ai_model", "claude"), new_summary_manual, new_summary_manual, sid),
            )
        else:
            conn.execute(
                "UPDATE sessions SET msg_count=?, tool_call_count=?, ai_model=? WHERE id=?",
                (metadata.get("msg_count", 0), metadata.get("tool_call_count", 0),
                 metadata.get("ai_model", "claude"), sid),
            )
        conn.commit()
        conn.close()
        return sid, True  # skipped=True: export must not be regenerated

    conn.execute("""
        INSERT OR REPLACE INTO sessions
          (id, created_at, ended_at, project_path, repo_name, branch, base_commit, agent_family,
           ai_model, summary, summary_manual, open_issues, msg_count, user_msg_count,
           tool_call_count, export_path, raw_jsonl_path, manually_reviewed)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
        effective_summary,
        summary_manual,
        open_issues,
        metadata.get("msg_count", 0),
        metadata.get("user_msg_count", 0),
        metadata.get("tool_call_count", 0),
        metadata.get("export_path", ""),
        metadata.get("raw_jsonl_path", ""),
        0,  # manually_reviewed resets to 0 on fresh write (force=True path)
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
        # event:* pseudo-paths belong in session_events, not session_artifacts
        if (a.get("file_path") or "").startswith("event:"):
            continue
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

    for m in _dedupe_adjacent_messages(metadata.get("messages", [])):
        conn.execute("INSERT INTO session_messages (session_id, role, text, timestamp) VALUES (?,?,?,?)",
                     (sid, m.get("role", ""), m.get("text", ""), m.get("timestamp")))

    conn.commit()
    conn.close()
    return sid, False  # skipped=False: full write completed

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
        metadata.get("summary_manual") or metadata.get("summary", ""),
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
        "keep_summary": False,
        "force": False,
        "tool_ids": None,
    }
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--help":
            print(__doc__)
            sys.exit(0)
        if arg == "--keep-summary":
            opts["keep_summary"] = True
            i += 1
            continue
        if arg == "--force":
            opts["force"] = True
            i += 1
            continue
        if "=" in arg and arg.startswith("--"):
            key, value = arg.split("=", 1)
        else:
            key, value = arg, None

        if key in ("--agent", "--cwd", "--summary", "--model", "--jsonl", "--tool-ids"):
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
            elif key == "--tool-ids":
                opts["tool_ids"] = value
            continue

        raise SystemExit(f"Unknown argument: {arg}")

    return opts

def cmd_archive_current(argv):
    opts = parse_archive_current_args(argv)

    if opts["jsonl"]:
        session_info = {"jsonl_path": str(Path(opts["jsonl"]).expanduser())}
    else:
        session_info = find_current_jsonl(cwd=opts["cwd"], agent_family=opts["agent"])

    tool_id_whitelist = None
    if opts.get("tool_ids"):
        try:
            ids = json.loads(opts["tool_ids"])
            if isinstance(ids, list) and ids:
                tool_id_whitelist = set(ids)
        except (json.JSONDecodeError, TypeError):
            pass  # invalid JSON → fall back to sessionId filter

    data = parse_jsonl(session_info["jsonl_path"], tool_id_whitelist=tool_id_whitelist)
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
        sid, skipped = write_session(metadata, force=opts.get("force", False))
        if skipped:
            # Session is manually reviewed — do not overwrite the curated export.
            conn = get_db()
            export_path = conn.execute(
                "SELECT export_path FROM sessions WHERE id=?", (sid,)
            ).fetchone()["export_path"]
            conn.close()
        else:
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
    sid, _   = write_session(metadata)
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
    conn.commit()
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
