"""Agent loop for the Pendula coding agent.

Dispatches OpenAI function-calling tool calls to registered handlers.
"""

from openai.types.chat import ChatCompletionMessageFunctionToolCall

from .config import MAX_TOKENS, MODEL, SYSTEM, get_client
from .logging import get_logger
from .tools import TOOL_HANDLERS, TOOLS

_log = get_logger("pendula.agent")


def agent_loop(messages: list[dict[str, str]]) -> None:
    """Run the agent loop: send messages, handle tool calls, repeat.

    Continues until the model returns a non-tool-call response.
    *messages* is mutated in-place with each exchange.
    """
    client = get_client()
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],  # type: ignore — dict works at runtime
            tools=TOOLS,
            max_tokens=MAX_TOKENS,
        )
        msg = response.choices[0].message
        _log.debug("agent.response", content=str(msg.content)[:200])
        messages.append(msg.model_dump())

        if not msg.tool_calls:
            return

        results = []
        for tc in msg.tool_calls:
            if not isinstance(tc, ChatCompletionMessageFunctionToolCall):
                continue
            name = tc.function.name
            _log.info("tool.call", tool=name)

            entry = TOOL_HANDLERS.get(name)
            if entry is None:
                output = f"Unknown: {name}"
            else:
                model, handler = entry
                args = model.model_validate_json(tc.function.arguments)
                output = handler(**dict(args))

            _log.info("tool.result", tool=name, length=len(output))
            results.append({"role": "tool", "tool_call_id": tc.id, "content": output})

        messages.extend(results)
