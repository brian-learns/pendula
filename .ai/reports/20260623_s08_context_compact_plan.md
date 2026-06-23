# s08 Context Compact — Implementation Plan

## Goal
Add a four-layer context compression pipeline to the agent loop so the agent can work for long sessions without hitting context limits.

---

## Files to change

| File | Change | Reason |
|------|--------|--------|
| `src/pendula/compact.py` | New module: snip_compact, micro_compact, tool_result_budget, compact_history, reactive_compact + helpers | Compression logic |
| `src/pendula/config.py` | Add THRESHOLD, MAX_KEEP_MESSAGES, KEEP_RECENT_TOOL_RESULTS, etc. | Configuration constants |
| `src/pendula/models.py` | Add CompactArgs | Tool argument model |
| `src/pendula/tools.py` | Register `compact` tool | Model-initiated compaction |
| `src/pendula/agent.py` | Insert compression pipeline before each LLM call + reactive_compact catch | Integration with agent loop |
| `tests/test_compact.py` | New test file | Coverage |
| `tests/test_tools.py` | Update tool count (9) and keys | Existing tests |
| `HACKERS.md` | Add compact.py to module table | Documentation |
| `SPEC.md` | Mark s08 as ✅, update dependency/module tables | Spec accuracy |

---

## Design decisions & tradeoffs

### 1. Compression pipeline order
The four layers must run in this specific order:
1. **L3: tool_result_budget** — persist large results to disk FIRST (before micro replaces them)
2. **L1: snip_compact** — trim middle messages
3. **L2: micro_compact** — replace old tool results with placeholders
4. **L4: compact_history** — LLM summary if still over threshold

This order is intentional and matches the CC source.

### 2. Integration with agent loop
The compression pipeline runs **before each LLM call** in `agent_loop`. The reactive compact runs when `prompt_too_long` is caught. This modifies `agent.py` significantly — the loop gets a pre-processing step and a try/except around the API call.

### 3. Token estimation
Using character-count-based estimate (simple, per teaching version). Precise tokenizers are out of scope.

### 4. Transcripts & persisted output storage
- Transcripts go to `WORKDIR / ".transcripts"` (one file per compaction)
- Persisted large tool results go to `WORKDIR / ".task_outputs"` (one file per tool call)
- Directories are created on first use

### 5. Circuit breaker
- `compact_history`: 3 consecutive failures before stopping
- `reactive_compact`: 1 retry before raising exception

### 6. compact tool
A `compact` tool lets the model actively trigger compaction. The handler calls `compact_history` and returns a summary.

### 7. No circular imports
`compact.py` imports only from `config.py` and standard lib. `agent.py` imports compression functions from `compact.py`. Clean DAG.

---

## Dependency flow (updated)

```
config.py  (leaf)
    ↓
models.py  (depends on pydantic only)
    ↓
tools.py   (depends on .config, .models, .logging)
    ↓
hooks.py   (depends on .config)
    ↓
skills.py  (depends on .config)
    ↓
compact.py (depends on .config)
    ↓
subagent.py (depends on .config, .hooks, .tools via deferred import)
    ↓
agent.py   (depends on .config, .hooks, .tools, .logging, .skills, .compact)
    ↓
repl.py    (depends on .agent, .hooks)
    ↓
cli.py     (depends on .repl, .logging)
```

---

## Implementation order

1. Create `compact.py` — all compression functions + helpers
2. Add config constants to `config.py`
3. Register `compact` tool in `tools.py` (add `CompactArgs` to models)
4. Update `agent.py` — insert compression pipeline, wrap API call in try/except
5. Add tests (`test_compact.py`, update `test_tools.py`)
6. Update docs (`HACKERS.md`, `SPEC.md`)
7. `make test` — all pass
8. Commit, user tests

---

## Questions for the user

None — plan is self-contained.
