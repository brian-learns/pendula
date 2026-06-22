"""Tool handler functions and registration for the Pendula coding agent.

Each handler is decorated with ``@tool`` which simultaneously:
1. Creates an OpenAI ``pydantic_function_tool`` definition
2. Registers the (Pydantic_model, handler) pair in ``TOOL_HANDLERS``
3. Appends the tool definition to ``TOOLS``

Usage
-----
    @tool(name="bash", description="Run a shell command.", model=BashArgs)
    def run_bash(command: str) -> str:
        ...
"""

from __future__ import annotations

import functools
import subprocess
from pathlib import Path
from typing import Callable, Type

import openai
from pydantic import BaseModel

from .config import WORKDIR
from .logging import get_logger, log_call
from .models import (
    BashArgs,
    EditFileArgs,
    GlobArgs,
    ReadFileArgs,
    TodoWriteArgs,
    WriteFileArgs,
)

# ═══════════════════════════════════════════════════════════
#  Registry
# ═══════════════════════════════════════════════════════════

TOOLS: list = []  # filled by @tool decorator
TOOL_HANDLERS: dict[str, tuple[Type[BaseModel], Callable]] = {}

_log = get_logger("pendula.tools")


def tool(name: str, description: str, model: Type[BaseModel]):
    """Decorator: register a handler function as an OpenAI tool.

    Parameters
    ----------
    name : str
        Tool name sent to the LLM.
    description : str
        Description sent to the LLM.
    model : Type[BaseModel]
        Pydantic model class for validating arguments.
    """

    def decorator(fn):
        """Register *fn* as a tool and return a logging-wrapped version."""
        tool_def = openai.pydantic_function_tool(
            name=name,
            description=description,
            model=model,
        )
        TOOLS.append(tool_def)
        TOOL_HANDLERS[name] = (model, fn)

        @functools.wraps(fn)
        @log_call(_log, event=f"tool.{name}")
        def wrapper(*args, **kwargs):
            """Call the tool handler and return its result."""
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ═══════════════════════════════════════════════════════════
#  Tool implementations
# ═══════════════════════════════════════════════════════════


@tool(name="bash", description="Run a shell command.", model=BashArgs)
def run_bash(command: str) -> str:
    """Execute a shell command inside the workspace directory.

    Dangerous commands are blocked by the permission hook (see hooks.py).
    """
    try:
        r = subprocess.run(  # noqa: S602
            command,
            shell=True,  # intentional: agent needs pipes, redirects, compound cmds
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"


def safe_path(p: str) -> Path:
    """Resolve *p* relative to *WORKDIR* and verify it does not escape."""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


@tool(name="read_file", description="Read file contents.", model=ReadFileArgs)
def run_read(path: str, limit: int | None = None) -> str:
    """Read a file and return its contents, optionally truncated to *limit* lines."""
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = [*lines[:limit], f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@tool(
    name="write_file",
    description="Write content to a file.",
    model=WriteFileArgs,
)
def run_write(path: str, content: str) -> str:
    """Write *content* to *path*, creating parent directories if needed."""
    try:
        file_path = safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


@tool(
    name="edit_file",
    description="Replace exact text in a file once.",
    model=EditFileArgs,
)
def run_edit(path: str, old_text: str, new_text: str) -> str:
    """Replace the first occurrence of *old_text* with *new_text* in *path*."""
    try:
        file_path = safe_path(path)
        text = file_path.read_text()
        if old_text not in text:
            return f"Error: text not found in {path}"
        file_path.write_text(text.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"


@tool(name="glob", description="Find files matching a glob pattern.", model=GlobArgs)
def run_glob(pattern: str) -> str:
    """Find files matching a glob pattern inside the workspace."""
    import glob as g

    try:
        results = [
            match
            for match in g.glob(pattern, root_dir=WORKDIR)
            if (WORKDIR / match).resolve().is_relative_to(WORKDIR)
        ]
        return "\n".join(results) if results else "(no matches)"
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════════
#  TODO system
# ═══════════════════════════════════════════════════════════

CURRENT_TODOS: list[dict] = []


def reset_todos() -> None:
    """Clear the global TODO list (used in tests)."""
    global CURRENT_TODOS
    CURRENT_TODOS = []


@tool(
    name="todo_write",
    description="Create and manage a task list. Call this first to plan steps, "
    "then update statuses as you work.",
    model=TodoWriteArgs,
)
def run_todo_write(todos: list) -> str:
    """Store *todos* in module-level state and print progress.

    *todos* items may be dicts or Pydantic ``TodoItem`` objects.
    """
    global CURRENT_TODOS
    # Convert to plain dicts for uniform handling
    CURRENT_TODOS = [
        {"content": t["content"], "status": t["status"]}
        if isinstance(t, dict)
        else {"content": t.content, "status": t.status}
        for t in todos
    ]

    lines = ["\n## Current Tasks"]
    for t in CURRENT_TODOS:
        icon = {"pending": " ", "in_progress": "▸", "completed": "✓"}[t["status"]]
        lines.append(f"  [{icon}] {t['content']}")
    print("\n".join(lines))
    return f"Updated {len(CURRENT_TODOS)} tasks"
