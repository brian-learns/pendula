# pendula

A lightweight Python coding agent that uses OpenAI function-calling (tool use) to execute shell commands, read/write/edit files, and glob within a workspace directory.

Based on [Learn Claude Code -- Harness Engineering for Real Agents](https://github.com/shareAI-lab/learn-claude-code) thanks [shareAI-lab](https://huggingface.co/shareAI)

I'm on step `s02` right now, I'm going to do a tag or branch for each chapter.

Just basically me learning to vibe code with [ds4-agent](https://github.com/antirez/ds4/) \*.  

\* I've got my own [`SearchXNG` branch](https://github.com/brian-learns/ds4/tree/SearXNG)


## Quick start

```bash
# Install dependencies
uv sync

# Copy and edit the environment file
cp env.example .env
# Set DEFAULT_MODEL to your OpenAI-compatible model

# Run the REPL
uv run pendula
```

## Commands

| `make` target | What it does |
|---|---|
| `make check` | Static analysis: ruff, bandit, vulture, refurb |
| `make test`  | `check` + pytest |
| `make clean` | Wipe cache files |

## License

MIT — see LICENSE.

## Progression
```
Each lesson adds one harness mechanism. Each mechanism has a motto.
s01   "One loop & Bash is all you need" — one tool + one loop = one agent ✅
s02   "Adding a tool means adding one handler" — the loop stays untouched; new tools register into the dispatch map ✅
s03   "Set boundaries first, then grant freedom" — check what can run, what must stop, and what needs approval
s04   "Hook around the loop, never rewrite the loop" — add extension points without changing the main loop
s05   "An agent without a plan drifts" — list the steps before starting; completion rate doubles
s06   "Big tasks split small, each subtask gets clean context" — subagents do the side work and bring back only the result
s07   "Load knowledge on demand, not upfront" — list skills first, expand them only when needed
s08   "Context always fills up -- have a way to make room" — multi-layer compaction strategies buy you infinite sessions
s09   "Remember what matters, forget what doesn't" — three subsystems: selection, extraction, consolidation
s10   "Prompts are assembled at runtime, not hardcoded" — section-based concatenation, loaded on demand
s11   "Errors aren't the end, they're the start of a retry" — retry, make room, or take another path when things fail
s12   "Big goals break into small tasks, ordered, persisted to disk" — a file-backed task graph that lays the groundwork for multi-agent coordination
s13   "Slow ops go background, agent keeps thinking" — background threads run commands; notifications inject on completion
s14   "Fire on schedule, no human kick needed" — trigger tasks automatically by time
s15   "Too big for one agent -- delegate to teammates" — persistent teammates + async mailboxes
s16   "Teammates need shared communication rules" — use a fixed request-reply format for coordination
s17   "Teammates check the board, claim work themselves" — no leader assigning one by one; self-organizing
s18   "Each works in its own directory, no interference" — tasks own goals, worktrees own directories, bound by ID
s19   "Not enough capability? Plug in more via MCP" — connect external tools into the same tool pool
s20   "Many mechanisms, one loop" — all previous mechanisms return to one complete harness
```

## Python

I'm also learning about `uv init --package` and modern python best practices.
