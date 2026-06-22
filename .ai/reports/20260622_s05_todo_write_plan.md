# s05 TodoWrite — Implementation Plan

## Goal
Give the Agent a planning tool (`todo_write`) so it lists steps before executing complex tasks. Add a nag reminder when the model hasn't updated its plan for 3 consecutive rounds.

---

## Files to change

| File | Change | Reason |
|------|--------|--------|
| `src/pendula/models.py` | Add `TodoWriteArgs` Pydantic model | Tool needs typed args |
| `src/pendula/tools.py` | Add `run_todo_write` handler + `CURRENT_TODOS` global | Tool handler + stateful todo list |
| `src/pendula/config.py` | Update `SYSTEM` to include planning guidance | Teach agent to plan first |
| `src/pendula/agent.py` | Add `rounds_since_todo` counter + reminder injection | Nag reminder after 3 rounds without todo_write |
| `tests/test_tools.py` | Add `TestRunTodoWrite` class | Coverage for new handler |
| `tests/test_agent.py` | Add test for nag reminder | Coverage for loop change |
| `HACKERS.md` | Mention `CURRENT_TODOS` global | Documentation |
| `SPEC.md` | Mark s05 as ✅, update module/dependency tables | Spec accuracy |

---

## Design decisions & tradeoffs

### 1. Nag reminder — inline vs hook
**Option A** (follow original): Put counter + reminder logic directly in `agent.py`. Simple, matches the teaching source exactly.
**Option B** (leverage hooks): Make it a `PreToolUse` hook that tracks rounds and injects a reminder. Cleaner separation of concerns.

**Choice**: Option A — the reminder is tightly coupled to the loop's message flow (injects a message *before* the next LLM call). A hook would need to fire between rounds, which doesn't fit the current hook events cleanly. We'll keep it inline to stay close to the pedagogical source.

### 2. `CURRENT_TODOS` — module-level mutable state
The todo list is stored in a module-level list. This is fragile in tests — state persists across test runs.

**Mitigation**: Provide a `reset_todos()` helper in `tools.py` for test teardown. The `conftest.py` can call it after each test that uses the todo system.

### 3. System prompt — hard-coded extension
The original appends "plan before executing" guidance to the system prompt. We'll do the same in `config.py` by extending the existing `SYSTEM` string.

**Tradeoff**: Hard-coded means the planning instruction is always present. Making it dynamic (e.g., a flag) would be over-engineering for s05.

### 4. Tool registration follows existing pattern
`run_todo_write` gets the `@tool` decorator just like the other 5 tools. No new registration machinery needed — the existing `TOOL_HANDLERS` dict and `TOOLS` list handle it.

---

## Implementation order

1. Create `s05_hooks` branch from `main`
2. Add `TodoWriteArgs` to `models.py`
3. Add `run_todo_write` + `CURRENT_TODOS` + `reset_todos` to `tools.py`
4. Update `SYSTEM` in `config.py`
5. Add nag reminder counter + injection to `agent.py`
6. Add tests
7. Update docs (`HACKERS.md`, `SPEC.md`)
8. `make test` — all pass
9. Commit, user tests, merge to `main`

---

## Questions for the user

None — the plan is self-contained. Ready to proceed.
