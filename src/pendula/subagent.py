"""Sub-agent system for the Pendula coding agent.

``spawn_subagent()`` creates an independent agent with a fresh message list,
restricted tool set (no ``task`` tool), and a 30-round safety limit.
It returns only the final conclusion text to the parent agent.

The sub-agent's tool calls still go through permission hooks —
context isolation does not bypass security.
"""

from __future__ import annotations

from types import SimpleNamespace

from .config import MAX_TOKENS, MODEL, get_client
from .hooks import trigger_hooks
from .logging import get_logger

_log = get_logger("pendula.subagent")

SUB_MAX_ROUNDS = 30

# Sub-agent system prompt — explicitly forbid delegation
SUB_SYSTEM = (
    "You are a sub-agent completing a subtask for a parent agent. "
    "Use tools to solve the task. Act, don't explain. "
    "Complete the task and return your final answer. "
    "Do not delegate further — you have no task tool."
)


def spawn_subagent(description: str) -> str:
    """Spawn an independent sub-agent, return its conclusion.

    Parameters
    ----------
    description : str
        The task description to give the sub-agent.

    Returns
    -------
    str
        The sub-agent's final message content, or an error message.
    """
    client = get_client()

    # Build restricted tool set at call time (avoids circular import)
    from .tools import TOOL_HANDLERS, TOOLS

    sub_tools = [t for t in TOOLS if t.get("name") != "task"]
    sub_handlers = {k: v for k, v in TOOL_HANDLERS.items() if k != "task"}

    messages: list[dict[str, str]] = [{"role": "user", "content": description}]

    for _round in range(SUB_MAX_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SUB_SYSTEM}, *messages],  # type: ignore — dict works at runtime
            tools=sub_tools,
            max_tokens=MAX_TOKENS,
        )
        msg = response.choices[0].message
        _log.debug("subagent.response", round=_round, content=str(msg.content)[:200])
        messages.append(msg.model_dump())

        if not msg.tool_calls:
            # Sub-agent finished
            break

        results = []
        for tc in msg.tool_calls:
            name = tc.function.name
            _log.info("subagent.tool.call", tool=name)

            entry = sub_handlers.get(name)
            if entry is None:
                output = f"Unknown: {name}"
            else:
                model, handler = entry
                args = model.model_validate_json(tc.function.arguments)
                tool_block = SimpleNamespace(name=name, input=dict(args))

                # Hook: PreToolUse — can block the tool call
                blocked = trigger_hooks("PreToolUse", tool_block)
                if blocked:
                    output = str(blocked)
                else:
                    output = handler(**dict(args))

                # Hook: PostToolUse — observe the result
                trigger_hooks("PostToolUse", tool_block, output)

            _log.info("subagent.tool.result", tool=name, length=len(output))
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": output,
                }
            )

        messages.extend(results)

    # Return the final assistant message, or error if hit limit
    if not msg.tool_calls:
        last = messages[-1]
        return last.get("content") or "(no output)"
    return "Error: Sub-agent exceeded safety limit"
