"""Agent loop for the Pendula coding agent.

Dispatches OpenAI function-calling tool calls to registered handlers.
"""

from openai.types.chat import ChatCompletionMessageFunctionToolCall

from .config import MODEL, SYSTEM, client
from .tools import TOOL_HANDLERS, TOOLS


def agent_loop(messages: list[dict[str, str]]) -> None:
    """Run the agent loop: send messages, handle tool calls, repeat.

    Continues until the model returns a non-tool-call response.
    *messages* is mutated in-place with each exchange.
    """
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, *messages],  # type: ignore — dict works at runtime
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
