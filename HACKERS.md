# HACKERS.md — Coding Rules for Pendula

These rules apply to **human developers and AI coding agents alike**.
They keep the codebase consistent, safe, and easy to maintain.

---

## 1. Architecture

### Module responsibilities

| Module | Responsibility | May import from |
|--------|---------------|----------------|
| `config.py` | Env loading, shared globals (`WORKDIR`, `MODEL`, `client`) | — (leaf module) |
| `models.py` *(future)* | Pydantic argument models | `pydantic` |
| `tools.py` | Tool handler functions + registry | `.config`, `.models` |
| `agent.py` | Agent loop (dispatch tool calls) | `.config`, `.tools` |
| `cli.py` | REPL / CLI entry point | `.agent` |

### Rules

- **No circular imports.** Modules import only from modules listed in the table above.
- **No `__init__.py` re-exports of internal symbols** beyond the public API (`main`, `__version__`).
- **No mutable module-level state** beyond `config.py` globals. Tools are stateless functions.

---

## 2. Code style

- **Line length:** 88 characters (Ruff default).
- **Naming:** `snake_case` for functions and variables, `PascalCase` for classes.
- **Docstrings:** Every module, public function, and class gets a brief docstring (triple-quoted).
- **Type hints:** Required on all function signatures.
- **Imports:** `isort`-style (stdlib → third-party → local). Ruff enforces this.
- **Error handling:** Use `try`/`except Exception` in tool functions; return error strings to the model, never `raise` across module boundaries.

---

## 3. Testing

- **Run** `make test` before pushing. It runs ruff, bandit, vulture, refurb, then pytest.
- **New tests** go in `tests/` matching the module name (`test_tools.py`, `test_agent.py`, etc.).
- **Use** `pytest` features (`tmp_path`, `monkeypatch`) for temp files and env isolation.
- **Mock** the OpenAI client in agent tests; don't call the real API.
- **Assertions** are allowed (Ruff ignores `S101` in test files).

---

## 4. Tools pattern

Each tool consists of:
1. A **handler function** (e.g. `run_bash`) that takes typed params and returns `str`.
2. A **Pydantic model** for its arguments (e.g. `BashArgs`).
3. A **registration** in `TOOL_HANDLERS` dict and `TOOLS` list.

When adding a new tool:
- Add the handler in `tools.py`.
- Add the Pydantic model (or add to `models.py` once split).
- Register in `TOOL_HANDLERS` and `TOOLS`.
- Add tests in `tests/test_tools.py`.
- Run `make test`.

---

## 5. Logging (once `logging.py` exists)

- Use the `AgentLogger` bound logger for agent-loop tracing.
- Use `log_call` decorator on tool handlers for entry/exit logging.
- Never `print()` for debug info — use the logging framework.

---

## 6. Safety

- `safe_path()` must be called on every file path before touching the filesystem.
- Dangerous shell commands are blocked by `run_bash`.
- The workspace is always `WORKDIR` (the project root). Paths that escape are rejected.

---

## 7. Git workflow

- Commits should be small and focused.
- Commit messages: short summary line, then blank line, then body if needed.
- `s02.py` has been removed; all code lives in `config.py`, `models.py`, `tools.py`, `agent.py`, `cli.py`.

---

*Last updated: June 2026*
