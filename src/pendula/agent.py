"""Agent loop for the Pendula coding agent.

Dispatches OpenAI function-calling tool calls to registered handlers.
Hook calls are inserted at key points:
- ``PreToolUse`` / ``PostToolUse`` around each tool execution
- ``Stop`` when the loop exits

Context compression runs before each LLM call:
- L3: tool_result_budget (persist large results to disk)
- L1: snip_compact (trim middle messages)
- L2: micro_compact (old result placeholders)
- L4: compact_history (LLM summary, only if still over threshold)

If the API returns prompt_too_long, reactive_compact kicks in.
"""

from types import SimpleNamespace

from openai.types.chat import ChatCompletionMessageFunctionToolCall

from .compact import (
    MAX_REACTIVE_RETRIES,
    THRESHOLD_CHARS,
    compact_history,
    estimate_token_count,
    reactive_compact,
    run_compression_pipeline,
)
from .config import MAX_TOKENS, MODEL, get_client
from .hooks import trigger_hooks
from .logging import get_logger
from .skills import SYSTEM
from .tools import TOOL_HANDLERS, TOOLS

_log = get_logger("pendula.agent")

REMINDER_INTERVAL = 3


def agent_loop(messages: list[dict[str, str]]) -> None:
    """Run the agent loop: send messages, handle tool calls, repeat.

    Continues until the model returns a non-tool-call response.
    *messages* is mutated in-place with each exchange.
    Hook events fire around tool execution (``PreToolUse``, ``PostToolUse``)
    and when the loop ends (``Stop``).

    Context compression runs before each LLM call:
    - budget → snip → micro (0 API calls)
    - compact_history (1 API call) if still over threshold
    - reactive_compact on prompt_too_long error

    A nag reminder is injected when the model hasn't called ``todo_write``
    for ``REMINDER_INTERVAL`` consecutive rounds.
    """
    client = get_client()
    rounds_since_todo = 0
    reactive_retries = 0

    while True:
        # ── Compression pipeline (cheap first, expensive last) ──
        messages[:] = run_compression_pipeline(messages)

        if estimate_token_count(messages) > THRESHOLD_CHARS:
            messages[:] = compact_history(messages)

        # ── LLM call ──
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": SYSTEM}, *messages],  # type: ignore — dict works at runtime
                tools=TOOLS,
                max_tokens=MAX_TOKENS,
            )
            reactive_retries = 0
        except Exception as exc:
            _log.warning("agent.error", error=str(exc)[:200])
            ptl = "prompt_too_long"
            if ptl in str(exc).lower() and reactive_retries < MAX_REACTIVE_RETRIES:
                messages[:] = reactive_compact(messages)
                reactive_retries += 1
                continue
            raise

        msg = response.choices[0].message
        _log.debug("agent.response", content=str(msg.content)[:200])
        messages.append(msg.model_dump())

        if not msg.tool_calls:
            # Loop is about to exit — fire Stop hooks
            blocked = trigger_hooks("Stop", messages)
            if blocked:
                messages.append({"role": "user", "content": str(blocked)})
                continue
            return

        results = []
        called_todo = False
        did_compact = False

        for tc in msg.tool_calls:
            if not isinstance(tc, ChatCompletionMessageFunctionToolCall):
                continue
            name = tc.function.name
            _log.info("tool.call", tool=name)

            if name == "todo_write":
                called_todo = True

            # ── Special: compact tool triggers history compaction ──
            if name == "compact":
                messages[:] = compact_history(messages)
                results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": "[Compacted. History summarized.]",
                    }
                )
                did_compact = True
                continue

            entry = TOOL_HANDLERS.get(name)
            if entry is None:
                output = f"Unknown: {name}"
            else:
                model, handler = entry
                args = model.model_validate_json(tc.function.arguments)

                # Wrap args in a block-like object for hooks (expects .name, .input)
                tool_block = SimpleNamespace(name=name, input=dict(args))

                # Hook: PreToolUse — can block the tool call
                blocked = trigger_hooks("PreToolUse", tool_block)
                if blocked:
                    output = str(blocked)
                else:
                    output = handler(**dict(args))

                # Hook: PostToolUse — observe the result
                trigger_hooks("PostToolUse", tool_block, output)

            _log.info("tool.result", tool=name, length=len(output))
            results.append({"role": "tool", "tool_call_id": tc.id, "content": output})

        messages.extend(results)

        # ── If compact was called, start fresh with compacted context ──
        if did_compact:
            continue

        # Nag reminder: if todo_write wasn't called this round, increment counter
        if called_todo:
            rounds_since_todo = 0
        else:
            rounds_since_todo += 1

        if rounds_since_todo >= REMINDER_INTERVAL and messages:
            messages.append(
                {
                    "role": "user",
                    "content": "<reminder>Update your todos.</reminder>",
                }
            )
            rounds_since_todo = 0
