# Pendula — Project Spec

A Python best-practices reimplementation of [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code),
one pedagogical step at a time.

---

## Vision

Build a production-quality coding agent harness by working through all 20 lessons
from the original repo, but **in Python with proper project hygiene**:
separate modules, type hints, logging, tests, static analysis, and a
`make test` gate.

Each lesson introduces one new mechanism.  The harness grows incrementally;
no lesson rewrites the previous one.

---

## Current state

| Lesson | Status | What it delivers |
|--------|--------|-----------------|
| s01 — One loop & Bash is all you need | ✅ Merged into `config.py`, `tools.py`, `agent.py` | Agent loop + `bash` tool |
| s02 — Adding a tool means adding one handler | ✅ Merged into `models.py`, `tools.py` | 5 tools (bash, read, write, edit, glob) via typed dispatch |
| s03–s20 | ❌ Not started | Branches from `main` |

---

## Branch strategy

Going forward **each lesson gets its own branch**, created from `main`:

```
s03_permission    ─▶  main
s04_hooks          ─▶  main
s05_todo_write     ─▶  main
...
```

Each branch implements the lesson's mechanism, then is reviewed and merged.
The `main` branch always contains the accumulated harness so far.

---

## Architecture

### Module layout (current)

```
src/pendula/
├── config.py      — env loading, shared globals (WORKDIR, MODEL, client)
├── models.py      — Pydantic argument models for tools
├── tools.py       — tool handlers + @tool decorator + registries
├── agent.py       — agent loop (dispatch loop)
├── logging.py     — structured logging (structlog)
├── cli.py         — REPL entry point with --loglevel
├── __init__.py    — package entry
└── __main__.py    — python -m support
```

### Dependency flow (no circular imports)

```
config.py  (leaf)
    ↓
models.py  (depends on pydantic only)
    ↓
tools.py   (depends on .config, .models, .logging)
    ↓
agent.py   (depends on .config, .tools, .logging)
    ↓
cli.py     (depends on .agent, .logging)
```

### Tool pattern

Each tool = 1 handler function + 1 Pydantic model + 1 `@tool` decorator registration.
New lessons will add new mechanisms (permissions, hooks, subagents, memory, etc.)
without changing existing tools or the main loop.

---

## Lesson roadmap (s03–s20)

| # | Lesson title | Core mechanism |
|---|-------------|----------------|
| 3 | Set boundaries first, then grant freedom | Permission system — allow/deny/approve per tool |
| 4 | Hook around the loop, never rewrite the loop | Extension points (before/after tool call) |
| 5 | An agent without a plan drifts | Step planning — list steps before execution |
| 6 | Big tasks split small, each subtask gets clean context | Subagents — spawn child agents for subtasks |
| 7 | Load knowledge on demand, not upfront | Skill loading — lazy-load skill definitions |
| 8 | Context always fills up — have a way to make room | Context compaction — multi-layer compression |
| 9 | Remember what matters, forget what doesn't | Memory — selection, extraction, consolidation |
| 10 | Prompts are assembled at runtime, not hardcoded | Dynamic system prompt assembly |
| 11 | Errors aren't the end, they're the start of a retry | Error recovery — retry/fallback strategies |
| 12 | Big goals break into small tasks, ordered, persisted to disk | Task graph — file-backed task decomposition |
| 13 | Slow ops go background, agent keeps thinking | Background tasks — async command execution |
| 14 | Fire on schedule, no human kick needed | Cron scheduler — time-triggered tasks |
| 15 | Too big for one agent — delegate to teammates | Agent teams — persistent sub-agents + mailboxes |
| 16 | Teammates need shared communication rules | Team protocols — fixed request-reply format |
| 17 | Teammates check the board, claim work themselves | Self-organizing — no leader assignment |
| 18 | Each works in its own directory, no interference | Worktrees — per-task isolated directories |
| 19 | Not enough capability? Plug in more via MCP | MCP tools — external tool integration |
| 20 | Many mechanisms, one loop | Final integration — all mechanisms in one harness |

---

## Key conventions

- **`make test`** must pass before merge (ruff + bandit + vulture + refurb + interrogate + pytest)
- **`HACKERS.md`** governs AI-agent and human coding rules
- **No circular imports** — dependency direction is `config → models → tools → agent → cli`
- **New lessons add modules, never rewrite existing ones**
- **`s02.py` is gone** — all code lives in the module structure above
- **Branch per lesson** — branches are named `s<number>_<descriptor>`

---

## Environment

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DEFAULT_MODEL` | ✅ Yes | — | Model name for chat completions |
| `MAX_TOKENS` | ❌ No | `8000` | Max tokens per completion |
| `OPENAI_BASE_URL` | ❌ No | *(see .env)* | API endpoint (llama.cpp, OpenRouter, etc.) |
| `OPENAI_API_KEY` | ❌ No | `"False"` | API key (disabled for local backends) |

---

*Living spec — update as the project evolves.*
