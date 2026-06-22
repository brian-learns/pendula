"""Tool functions and Pydantic models for the Pendula coding agent.

Provides safe file operations, shell execution, glob matching,
and typed Pydantic argument models used for OpenAI function-calling dispatch.
"""

import subprocess
from pathlib import Path

import openai
from pydantic import BaseModel, Field

from .config import WORKDIR

# ═══════════════════════════════════════════════════════════
#  Tool implementations
# ═══════════════════════════════════════════════════════════


def run_bash(command: str) -> str:
    """Execute a shell command inside the workspace directory.

    Dangerous commands (rm -rf /, sudo, shutdown, etc.) are blocked.
    """
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
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


def run_read(path: str, limit: int | None = None) -> str:
    """Read a file and return its contents, optionally truncated to *limit* lines."""
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = [*lines[:limit], f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def run_write(path: str, content: str) -> str:
    """Write *content* to *path*, creating parent directories if needed."""
    try:
        file_path = safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


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
#  Pydantic argument models for OpenAI function calling
# ═══════════════════════════════════════════════════════════


class BashArgs(BaseModel):
    command: str = Field(..., description="The shell command to run.")


class ReadFileArgs(BaseModel):
    path: str = Field(..., description="The path to the file to read.")
    limit: int | None = Field(
        default=None, description="Maximum number of lines to return."
    )


class WriteFileArgs(BaseModel):
    path: str = Field(..., description="The path to write to.")
    content: str = Field(..., description="The content to write.")


class EditFileArgs(BaseModel):
    path: str = Field(..., description="The path to the file to edit.")
    old_text: str = Field(..., description="The exact text to find and replace.")
    new_text: str = Field(..., description="The replacement text.")


class GlobArgs(BaseModel):
    pattern: str = Field(..., description="The glob pattern to search for.")


# ═══════════════════════════════════════════════════════════
#  OpenAI tool definitions
# ═══════════════════════════════════════════════════════════

bash_tool = openai.pydantic_function_tool(
    name="bash",
    description="Run a shell command.",
    model=BashArgs,
)
read_tool = openai.pydantic_function_tool(
    name="read_file",
    description="Read file contents.",
    model=ReadFileArgs,
)
write_tool = openai.pydantic_function_tool(
    name="write_file",
    description="Write content to a file.",
    model=WriteFileArgs,
)
edit_tool = openai.pydantic_function_tool(
    name="edit_file",
    description="Replace exact text in a file once.",
    model=EditFileArgs,
)
glob_tool = openai.pydantic_function_tool(
    name="glob",
    description="Find files matching a glob pattern.",
    model=GlobArgs,
)

TOOLS = [bash_tool, read_tool, write_tool, edit_tool, glob_tool]

# Typed dispatch: each entry is (Pydantic_model, handler_fn)
# Args parsed through model_validate_json() for validation
TOOL_HANDLERS = {
    "bash": (BashArgs, run_bash),
    "read_file": (ReadFileArgs, run_read),
    "write_file": (WriteFileArgs, run_write),
    "edit_file": (EditFileArgs, run_edit),
    "glob": (GlobArgs, run_glob),
}
