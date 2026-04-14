# Session Archive

**Forensic-grade session archiver for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).** Captures every tool call, artifact, diff, event, and decision from your AI coding sessions into a structured SQLite database — before the context window forgets.

Built entirely with Claude Code. Zero external dependencies. Single Python file.

> *"Every AI session is institutional knowledge. Without an archive, it evaporates the moment the conversation ends."*

## Why

Claude Code sessions produce deep technical work — architectural decisions, multi-file refactors, bug investigations, code reviews. But once the context window scrolls past, that knowledge is gone. You can't search it, you can't analyze it, you can't learn from patterns across sessions.

Session Archive solves this by parsing Claude Code's native JSONL transcripts and extracting structured metadata:

- **What files were touched** — artifacts with action classification (created / modified / deleted / moved)
- **What changed** — unified diffs from both git and synthetic sources (Edit tool old_string/new_string)
- **What tasks were worked on** — T### references extracted from tool calls, not prose
- **What happened** — events (deploy, tests_run, commit_made, code_review, handoff_read...)
- **What tools were used** — domain tags derived from actual tool calls via EvidenceAccumulator
- **Full transcript** — every message preserved in markdown for human review

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Evidence-based extraction** | Tags, tasks, events derived from tool call structure — not regex on conversation text. Eliminates context drift and phantom classifications. |
| **EvidenceAccumulator** | Single-pass over tool calls collects write paths, read paths, bash commands, skill names. All downstream extractors use this as source of truth. |
| **Archive boundary** | Detects `/archive-session` calls in tool history to avoid capturing previous sessions archived within the same conversation. |
| **Session boundary via `--tool-ids`** | When a single JSONL contains multiple conversations, tool call IDs from the current session scope the extraction precisely. |
| **Zero dependencies** | Pure Python 3 stdlib. Works on any machine with Python 3 — no virtualenv, no pip install. Critical for hook/skill integration. |
| **SQLite + WAL** | Append-only log data, concurrent reads during writes, single-file backup (`cp sessions.db sessions.db.bak`). |
| **Markdown exports** | Human-readable transcripts alongside the database. Shareable without DB access. |

## Quick Start

### 1. Archive from Claude Code chat

```
/archive-session
```

The included [Claude Code skill](skills/archive-session.md) handles everything: finds the JSONL, generates a summary, extracts metadata, writes to DB, exports markdown.

Install the skill:
```bash
cp skills/*.md ~/.claude/commands/
```

### 2. Archive from command line

```bash
python3 session_archive.py archive-current --cwd /path/to/project --summary "Implemented auth module"
```

### 3. Query your session history

```bash
# Quick stats
python3 session_archive.py stats

# Analytics dashboard
python3 analyze.py

# Individual reports
python3 analyze.py projects    # activity by project
python3 analyze.py tasks       # which tasks span multiple sessions
python3 analyze.py timeline    # daily activity
python3 analyze.py artifacts   # most-modified files
python3 analyze.py events      # deploy/test/commit frequency

# Deep dive into a project
python3 analyze.py deep MyProject

# Arbitrary SQL
python3 analyze.py query "SELECT repo_name, COUNT(*) as sessions FROM sessions GROUP BY repo_name ORDER BY sessions DESC"
```

### 4. Web dashboard (optional)

```bash
pip install datasette
datasette data/sessions.db
# → http://localhost:8001
```

## Architecture

```
Claude Code session
    │
    │  ~/.claude/projects/<project-hash>/<session-id>.jsonl
    │
    ▼
session_archive.py archive-current
    ├── detect_jsonl_format() → claude | codex
    ├── parse JSONL → messages + tool_calls
    ├── EvidenceAccumulator (single pass over tool_calls)
    │   ├── write_paths, read_paths, bash_calls
    │   ├── skill_names, task_file_edits
    │   └── archive_boundary detection
    ├── extract artifacts (with git-status enrichment)
    ├── extract events (evidence-based)
    ├── extract tasks (from tool calls, not prose)
    ├── extract tags (domain, skill, model)
    └── write_session_to_db() + export_markdown()
         │
         ├── data/sessions.db      (SQLite, WAL mode)
         └── data/exports/         (markdown transcripts)
              └── 2026-04-14_MyProject_claude_a1b2c3d4.md
```

## Database Schema

```sql
sessions (
  id, created_at, ended_at, project_path, repo_name, branch,
  base_commit, agent_family, ai_model,
  summary, summary_manual, open_issues,
  msg_count, user_msg_count, tool_call_count,
  export_path, raw_jsonl_path, manually_reviewed
)

session_tags      (session_id, category, value)         -- project | domain | model | skill
session_tasks     (session_id, task_id, actions)         -- extracted from tool calls
session_artifacts (session_id, file_path, action,        -- created | modified | deleted
                   is_code, is_doc, content, diff)
session_events    (session_id, event_type, detail)       -- deploy, tests_run, commit_made...
session_messages  (session_id, role, text, timestamp)    -- full transcript
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `archive-current [flags]` | Find current session, parse, save to DB |
| `parse <jsonl>` | Parse JSONL → stdout JSON |
| `write <metadata.json>` | Write session from JSON → DB + markdown |
| `stats` | Print session statistics |
| `query <sql>` | Run arbitrary SELECT → stdout JSON |

### Flags for `archive-current`

| Flag | Description |
|------|-------------|
| `--agent auto\|claude\|codex` | Agent type (default: auto) |
| `--cwd <path>` | Working directory (default: current) |
| `--summary <text>` | Session summary |
| `--model <model>` | AI model name |
| `--jsonl <path>` | Explicit JSONL path (default: autodetect) |
| `--tool-ids <json>` | Tool call IDs for session boundary |

## Claude Code Skills

Two [custom slash commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands) included in [`skills/`](skills/):

| Skill | Description |
|-------|-------------|
| `/archive-session` | Archives the current session — finds JSONL, generates summary, extracts metadata, writes to DB |
| `/verify-archive` | Verifies the last archive entry against known issues and auto-fixes what it can |

## Compatibility

| Environment | Support |
|-------------|---------|
| **Claude Code (CLI)** | Full — JSONL parsed automatically |
| OpenAI Codex | Partial — metadata only |

## Project Structure

```
session_archive.py     ← main CLI, single file, zero dependencies
analyze.py             ← analytics reports over sessions.db
skills/
  archive-session.md   ← Claude Code slash command
  verify-archive.md    ← archive verification slash command
data/
  sessions.db          ← SQLite database (gitignored)
  exports/             ← markdown transcripts (gitignored)
docs/
  SA-architecture.md   ← technical deep dive
  SA-HANDOFF.md        ← project status, known issues, backlog
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_ARCHIVE_DB_PATH` | `<script_dir>/data/sessions.db` | SQLite database path |
| `SESSION_ARCHIVE_EXPORT_DIR` | `<script_dir>/data/exports` | Markdown export directory |

## License

MIT
