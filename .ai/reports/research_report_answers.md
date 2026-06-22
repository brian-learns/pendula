# Research Report — Pendula Refactoring Next Steps

## 1. Logging Framework (`logging.py`)

### Decision: Use Python's built-in `logging` with structured JSON output via `structlog`

**Options considered:**

| Approach | Pros | Cons |
|----------|------|------|
| **stdlib `logging`** | Zero dependencies, well-known | Hard to get structured JSON, verbose config |
| **`structlog`** | Native JSON output, chain-of-thought tracing, context binding, canonical log-line pattern | Adds dependency, learning curve |
| **`loguru`** | Simpler API, prettier output | Less structured, not ideal for tracing |

**Recommendation:** Add `structlog` to `pyproject.toml`. It supports:
- **Bound loggers** — bind context (e.g., tool name, call ID) incrementally
- **Canonical log lines** — one log entry per agent loop iteration
- **JSON output** — machine-parseable for debugging
- **Standard-library bridging** — `structlog` can wrap stdlib for library code

### Stub design for `logging.py`:

```
logging.py
├── LoggerFactory          — creates per-module loggers with module prefix
├── AgentLogger            — bound logger for agent loop (tool_call_id, tool_name)
├── log_call               — decorator to log function entry/exit + duration
└── configure_logging      — one-shot setup: level, format (JSON/dev-friendly)
```

**Questions:**
1. Should tracing go to stderr while normal logs go to stdout? (Standard 12-factor: logs to stdout, diagnostics to stderr.)
✅ OK
2. Do we want a `--verbose` CLI flag to control log level at runtime?
》 how about --loglevel LEVEL where LEVEL such as DEBUG INFO WARNING etc.

---

## 2. Making `tools.py` Smaller / Less Boilerplate

### Current pain points (176 lines)

| Pain point | Lines | Why it's repetitive |
|-----------|-------|---------------------|
| Pydantic model classes (5) | ~25 | Each is 4–6 lines with `Field(..., description=…)`. Descriptions are boilerplate. |
| `openai.pydantic_function_tool()` calls (5) | ~25 | Each is 4 lines: name, description, model. Name/description often duplicate the model docstring. |
| `TOOL_HANDLERS` dict | ~12 | Maps name → (model, handler). Could be auto-generated. |
| `TOOLS` list | ~3 | Just the 5 tool objects. Could be auto-generated. |

### Options to reduce boilerplate

**Option A — Dataclass-style Pydantic with `create_model`**
Use `pydantic.create_model()` to generate models from a dict schema, cutting model classes from 25 lines to ~5.

**Tradeoff:** Loses IDE autocomplete on model fields; harder to maintain if models grow complex.

**Option B — Registry pattern with decorators**
Define a `@tool` decorator that simultaneously:
1. Builds the Pydantic model from type annotations
2. Calls `openai.pydantic_function_tool()`
3. Registers in `TOOL_HANDLERS` and `TOOLS`

Example from the reference project (Kubaski 2025) uses a simpler lambda-based `TOOL_HANDLERS` but still requires manual tool definitions. The decorator pattern would eliminate the repetitive `pydantic_function_tool()` calls.

**Option C — Split models into `models.py`** (like the reference example)
Separate `tools.py` into:
- `models.py` — Pydantic argument models only
- `tools.py` — handler functions + registry

**Tradeoff:** More files, but each is shorter and has a single responsibility.

**Option D — Auto-discover tools via `__init__`**
Use `inspect` or `__subclasses__` to auto-register tools. Fragile and over-engineered for 5 tools.

### Recommendation: **Option B + Option C together**
✅ OK

Create a `models.py` with the 5 argument models, then use a `@tool` decorator in `tools.py` to eliminate the repetitive `pydantic_function_tool()` / `TOOL_HANDLERS` / `TOOLS` boilerplate. The decorator would look like:

```python
# Decorator approach
_TOOL_HANDLERS: dict[str, tuple[type[BaseModel], Callable]] = {}
_TOOLS: list[object] = []

def tool(name: str, description: str):
    """Decorator that registers a function as an OpenAI tool."""
    def decorator(fn):
        # Derive Pydantic model from fn's parameter annotations
        model = _build_model_from_annotations(fn)
        tool_def = openai.pydantic_function_tool(name=name, description=description, model=model)
        _TOOLS.append(tool_def)
        _TOOL_HANDLERS[name] = (model, fn)
        return fn
    return decorator
```

This reduces `tools.py` from ~176 lines to ~60 lines (handlers + decorator).

**Questions:**
1. Should `models.py` be a separate file, or keep models inline with handlers? (Reference example uses separate `models.py`.)
》I think seperating it makes sense, the pydantic models I think can be used for more than tools
2. Is the decorator approach worth the indirection for only 5 tools? (Tradeoff: simplicity vs. future scalability.)
》sure
3. Could we use `pydantic.dataclasses` instead of `BaseModel` for simpler syntax?
》I don't know how to evaluate, feel free to investigate further and decide

---

## 3. Additional Observations
》let's note and defer on these issues

### `agent.py` — `max_tokens` is hardcoded (8000)
Should be configurable via `config.py` or environment variable.
》let's move default to config.py but let it be set in enviroment as well?

### `cli.py` — REPL loop is duplicated from the old `s02.py` `__main__` block
Could be simplified by having `cli.py` import from `s02.py`'s `__main__` block, but `s02.py` is now empty. Consider moving the REPL logic into a reusable function.
》let's continue to defer, but please write a ./cli_issue.md for more details for review

### `config.py` — `client = openai.OpenAI()` is eager-initialized at import time
Could be lazy-loaded to avoid issues in test environments where `.env` may not be present.
》sounds good

### Tests — `test_config.py` depends on the real `.env` file
The `test_model_from_env` test will fail if `DEFAULT_MODEL` is not set. Consider adding a `conftest.py` with `monkeypatch` fixture to set env vars for testing.
》sounds good

---

## Summary of Proposed Changes (next turn)

1. **Create `logging.py`** with `structlog` — stub with `LoggerFactory`, `AgentLogger`, `configure_logging`
2. **Add `structlog` to `pyproject.toml`** dependencies
3. **Create `models.py`** — extract Pydantic argument models from `tools.py`
4. **Refactor `tools.py`** — use `@tool` decorator to eliminate boilerplate; import models from `models.py`
5. **Move `max_tokens` to `config.py`**
6. **Add `conftest.py`** — `monkeypatch` env vars for test isolation
7. **Update `cli.py`** — reuse REPL logic from a shared function

No code has been edited this turn — this report is for review and approval before proceeding.
