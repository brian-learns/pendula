# s06 Subagent — Implementation Plan

## Goal
Give the Agent a `task` tool that spawns an independent sub-agent with a fresh message list, restricted tool set, and a 30-round safety limit. The sub-agent returns only a conclusion summary to the parent agent.

---

## Files to change

| File | Change | Reason |
|------|--------|--------|
| `src/pendula/models.py` | Add `TaskArgs` Pydantic model | Tool needs typed args |
| `src/pendula/subagent.py` | New module: `spawn_subagent()` + `SUB_SYSTEM` + sub-agent tool dispatch | Sub-agent loop logic |
| `src/pendula/tools.py` | Import `spawn_subagent`, register `task` tool | Tool handler registration |
| `tests/test_subagent.py` | New test file | Coverage |
| `tests/test_tools.py` | Update tool count (7) and keys | Existing tests |
| `HACKERS.md` | Add `subagent.py` to module table | Documentation |
| `SPEC.md` | Mark s06 as ✅, update module/dependency tables | Spec accuracy |

---

## Design decisions & tradeoffs

### 1. Where does `spawn_subagent` live?
**Option A**: In `tools.py` alongside other handlers. Simplest — fewer files. But `spawn_subagent` is conceptually a second agent loop, not a tool handler.

**Option B**: In `agent.py`. Symmetrical — it's a second agent loop. But creates a circular import: `tools.py` would need to import `spawn_subagent` from `agent.py`, and `agent.py` already imports from `tools.py`.

**Option C**: New `subagent.py` module. Clean separation, follows the "new lessons add modules" rule, avoids circular imports.

**Choice**: **C** — new `subagent.py` module.

### 2. Sub-agent tool restriction
The sub-agent should have bash/read/write/edit/glob but NOT task (no recursion). Two approaches:
- **Build a separate dict** at import time by copying `TOOL_HANDLERS` minus `task`. Cleaner, no runtime filtering.
- **Filter at runtime** in `spawn_subagent`. More flexible but adds per-call overhead.

**Choice**: Build `SUB_TOOL_HANDLERS` and `SUB_TOOLS` once at import time.

### 3. Sub-agent's system prompt
The sub-agent needs a prompt that says "complete the task, do not delegate further." This lives in `subagent.py` as `SUB_SYSTEM`.

### 4. Sub-agent still goes through hooks
Permission hooks, logging hooks, etc. all fire for sub-agent tool calls. Security is not bypassed.

### 5. Safety limit
30 rounds maximum. If the sub-agent exceeds this, return an error. The limit is hard-coded in `spawn_subagent`.

---

## Dependency flow

```
config.py  (leaf)
    ↓
models.py  (depends on pydantic only)
    ↓
tools.py   (depends on .config, .models, .logging)
    ↓
hooks.py   (depends on .config)
    ↓
subagent.py (depends on .config, .hooks, .tools, .logging)
    ↑        |
    |        v
    └────────┘
    (tools.py imports spawn_subagent from subagent.py;
     subagent.py imports TOOL_HANDLERS etc from tools.py)
```

This is a cross-dependency: `tools.py` imports from `subagent.py`, and `subagent.py` imports from `tools.py`. But it's not circular because the import graph is a DAG — `tools.py` does **not** import `subagent.py` for module-level symbols; instead, `tools.py` imports `spawn_subagent` from `subagent.py`, and `subagent.py` imports `TOOL_HANDLERS` etc. from `tools.py` at **function call time** (not module-level). This avoids circular imports.

Actually, this creates a circular import at module level if both import each other at the top level. To avoid this:
- `tools.py` does a **deferred import** of `spawn_subagent` inside the `tool` decorator or registration
- Or `subagent.py` does deferred imports of `TOOL_HANDLERS` etc. inside `spawn_subagent`

**Approach**: `tools.py` registers the task handler with a lambda / deferred import. `subagent.py` imports from tools inside `spawn_subagent()` at call time.

---

## Implementation order

1. Create `subagent.py` module with `spawn_subagent`, `SUB_SYSTEM`, `SUB_TOOL_HANDLERS`, `SUB_TOOLS`
2. Add `TaskArgs` to `models.py`
3. Register `task` tool in `tools.py` (deferred import to avoid circular deps)
4. Add tests (`test_subagent.py`, update `test_tools.py`)
5. Update docs (`HACKERS.md`, `SPEC.md`)
6. `make test` — all pass
7. Commit, user tests

---

## Questions for the user

None — plan is self-contained.
