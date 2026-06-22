#!/usr/bin/env python3
"""
s02_tool_use.py — Tool Use (typed dispatch via Pydantic)

Builds on s01: adds 4 new tools (read_file, write_file, edit_file, glob)
plus a typed dispatch map and path safety checks.

Dispatch pattern: TOOL_HANDLERS maps name → (Pydantic_model, handler_fn).
Args are parsed through model_validate_json() for validation + typed access.

Usage:
    pip install openai python-dotenv pydantic
    python s02_tool_use.py
"""

import os
import subprocess
from contextlib import suppress
from pathlib import Path

with suppress(ImportError):
    import readline

    readline.parse_and_bind("set bind-tty-special-chars off")
    readline.parse_and_bind("set input-meta on")
    readline.parse_and_bind("set output-meta on")
    readline.parse_and_bind("set convert-meta off")

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageFunctionToolCall
from pydantic import BaseModel, Field

load_dotenv(override=True)

WORKDIR = Path.cwd()
MODEL = os.environ["DEFAULT_MODEL"]
SYSTEM = (
    f"You are a coding agent at {WORKDIR}. "
    "Use tools to solve tasks. Act, don't explain."
)

client = openai.OpenAI()

# ═══════════════════════════════════════════════════════════
#  FROM s01 (unchanged)
# ═══════════════════════════════════════════════════════════


def run_bash(command: str) -> str:
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


# ═══════════════════════════════════════════════════════════
#  NEW in s02: 4 new tools + path safety
# ═══════════════════════════════════════════════════════════


def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


def run_read(path: str, limit: int | None = None) -> str:
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = [*lines[:limit], f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def run_write(path: str, content: str) -> str:
    try:
        file_path = safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


def run_edit(path: str, old_text: str, new_text: str) -> str:
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
#  NEW in s02: Pydantic models + tool definitions
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


# ═══════════════════════════════════════════════════════════
#  Typed dispatch: each entry is (Pydantic_model, handler_fn)
#  Args parsed through model_validate_json() for validation
# ═══════════════════════════════════════════════════════════

TOOL_HANDLERS = {
    "bash": (BashArgs, run_bash),
    "read_file": (ReadFileArgs, run_read),
    "write_file": (WriteFileArgs, run_write),
    "edit_file": (EditFileArgs, run_edit),
    "glob": (GlobArgs, run_glob),
}


# ═══════════════════════════════════════════════════════════
#  agent_loop — dispatch via typed TOOL_HANDLERS
# ═══════════════════════════════════════════════════════════


def agent_loop(messages: list[dict[str, str]]):
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],  # ty: ignore — dict works at runtime
            tools=TOOLS,
            max_tokens=8000,
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump())

        if not msg.tool_calls:
            return

        results = []
        for tc in msg.tool_calls:
            # Only handle function tool calls (pydantic_function_tool)
            if not isinstance(tc, ChatCompletionMessageFunctionToolCall):
                continue
            name = tc.function.name
            print(f"\033[33m> {name}\033[0m")

            # Look up (model, handler) in dispatch map
            entry = TOOL_HANDLERS.get(name)
            if entry is None:
                output = f"Unknown: {name}"
            else:
                model, handler = entry
                args = model.model_validate_json(tc.function.arguments)
                output = handler(**dict(args))

            print(str(output)[:200])
            results.append({"role": "tool", "tool_call_id": tc.id, "content": output})

        messages.extend(results)


if __name__ == "__main__":
    print("s02: Tool Use — typed dispatch via Pydantic models")
    print("输入问题,回车发送。输入 q 退出。\n")

    history = []
    while True:
        try:
            query = input("\033[36ms02 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        last_msg = history[-1]
        if last_msg["role"] == "assistant" and last_msg["content"]:
            print(last_msg["content"])
        print()
