"""Hook system for the Pendula coding agent.

Events
------
- ``UserPromptSubmit`` — before a user query reaches the LLM
- ``PreToolUse`` — before each tool execution (can block by returning a string)
- ``PostToolUse`` — after each tool execution (observes result, can't block)
- ``Stop`` — when the loop is about to exit

Usage
-----
    register_hook("PreToolUse", my_hook)
    trigger_hooks("PreToolUse", block)  # returns str | None
"""

from __future__ import annotations

from typing import Any, Callable

from .config import WORKDIR

# ═══════════════════════════════════════════════════════════
#  Registry
# ═══════════════════════════════════════════════════════════

HOOKS: dict[str, list[Callable]] = {
    "UserPromptSubmit": [],
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": [],
}

VALID_EVENTS = frozenset(HOOKS)


def register_hook(event: str, callback: Callable) -> None:
    """Register *callback* for *event*.

    Parameters
    ----------
    event : str
        One of ``UserPromptSubmit``, ``PreToolUse``, ``PostToolUse``, ``Stop``.
    callback : Callable
        Called when the event fires.  Return ``None`` to allow, a string to block.

    Raises
    ------
    ValueError
        If *event* is not a recognised hook event.
    """
    if event not in VALID_EVENTS:
        valid = sorted(VALID_EVENTS)
        raise ValueError(f"Unknown hook event: {event!r}. Valid: {valid}")
    HOOKS[event].append(callback)


def trigger_hooks(event: str, *args: Any) -> str | None:
    """Run all callbacks registered for *event*.

    Parameters
    ----------
    event : str
        Hook event name.
    *args : Any
        Arguments forwarded to each callback.

    Returns
    -------
    str or None
        The first non-``None`` return value from any callback, or ``None`` if all
        callbacks returned ``None``.  A non-``None`` return blocks the operation.
    """
    if event not in VALID_EVENTS:
        return None
    for callback in HOOKS[event]:
        result = callback(*args)
        if result is not None:
            return result
    return None


# ═══════════════════════════════════════════════════════════
#  Built-in hooks
# ═══════════════════════════════════════════════════════════

DENY_LIST = ["rm -rf /", "sudo", "shutdown", "reboot", "mkfs", "dd if=", "> /dev/sda"]
DESTRUCTIVE_KW = ["rm ", "> /etc/", "chmod 777", "chown", "> /dev/"]


def permission_hook(block: Any) -> str | None:
    """PreToolUse: deny-list check then user approval for destructive ops.

    Returns a denial message or ``None`` to allow.
    """
    name = block.name if hasattr(block, "name") else ""
    inp = block.input if hasattr(block, "input") else {}

    if name == "bash":
        command = inp.get("command", "")
        # Gate 1: hard deny list
        for pattern in DENY_LIST:
            if pattern in command:
                print(f"\n\033[31m⛔ Blocked: '{pattern}' is on the deny list\033[0m")
                return "Permission denied by deny list"

        # Gate 2: ask user for destructive keywords
        for kw in DESTRUCTIVE_KW:
            if kw in command:
                print("\n\033[33m⚠  Potentially destructive command\033[0m")
                print(f"   Tool: {name}({inp})")
                choice = input("   Allow? [y/N] ").strip().lower()
                if choice not in ("y", "yes"):
                    return "Permission denied by user"
                break

    # Gate 3: writing outside workspace
    if name in ("write_file", "edit_file"):
        path_str = inp.get("path", "")
        resolved = (WORKDIR / path_str).resolve()
        if not resolved.is_relative_to(WORKDIR):
            print("\n\033[33m⚠  Writing outside workspace\033[0m")
            print(f"   Tool: {name}({inp})")
            choice = input("   Allow? [y/N] ").strip().lower()
            if choice not in ("y", "yes"):
                return "Permission denied by user"

    return None


def log_hook(block: Any) -> None:
    """PreToolUse: log every tool call."""
    name = block.name if hasattr(block, "name") else ""
    inp = block.input if hasattr(block, "input") else {}
    args_preview = str(list(inp.values())[:2])[:60]
    print(f"\033[90m[HOOK] {name}({args_preview})\033[0m")
    return None


def large_output_hook(block: Any, output: str) -> None:
    """PostToolUse: warn on large output."""
    name = block.name if hasattr(block, "name") else ""
    if len(output) > 100000:
        size = len(output)
        print(f"\033[33m[HOOK] ⚠ Large output from {name}: {size} chars\033[0m")
    return None


def context_inject_hook(query: str) -> None:
    """UserPromptSubmit: log user input before it reaches the LLM."""
    print(f"\033[90m[HOOK] UserPromptSubmit: working in {WORKDIR}\033[0m")
    return None


def summary_hook(messages: list) -> None:
    """Stop: print session summary when loop is about to exit."""
    tool_count = sum(
        1
        for m in messages
        for b in (m.get("content") if isinstance(m.get("content"), list) else [])
        if isinstance(b, dict) and b.get("type") == "tool_result"
    )
    # Also count OpenAI-style tool results
    tool_count += sum(1 for m in messages if m.get("role") == "tool")
    print(f"\033[90m[HOOK] Stop: session used {tool_count} tool calls\033[0m")
    return None


# ═══════════════════════════════════════════════════════════
#  Register built-in hooks at import time
# ═══════════════════════════════════════════════════════════

register_hook("UserPromptSubmit", context_inject_hook)
register_hook("PreToolUse", permission_hook)
register_hook("PreToolUse", log_hook)
register_hook("PostToolUse", large_output_hook)
register_hook("Stop", summary_hook)
